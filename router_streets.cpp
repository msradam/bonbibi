// Real-street flood-aware routing: a RoutingKit Customizable Contraction
// Hierarchy (CCH) over an OSM car-routing graph, re-weighted from vkflood's
// depth raster. This is the production replacement for route.py's grid BFS —
// it routes on the actual street network and resolves the path to real OSM
// street names (from each way's "name" tag), not grid cells. The CCH topology
// is preprocessed once (weight-independent); each flood update is a fast
// re-customization, which is what makes real-time re-routing on a live flood
// viable.
//
// Requires RoutingKit (BSD-2, https://github.com/RoutingKit/RoutingKit) built
// under deps/routingkit, and an .osm.pbf car-routing extract for the target
// area (e.g. from Geofabrik) — see README for both.
//
// Usage: router_streets <graph.osm.pbf> <flood_depth.txt> <passable_depth_m>
#include <routingkit/osm_graph_builder.h>
#include <routingkit/osm_profile.h>
#include <routingkit/tag_map.h>
#include <routingkit/customizable_contraction_hierarchy.h>
#include <routingkit/nested_dissection.h>
#include <routingkit/inverse_vector.h>
#include <routingkit/timer.h>
#include <routingkit/constants.h>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <string>
#include <fstream>
#include <sstream>
using namespace RoutingKit;

int main(int argc, char** argv) {
    if (argc < 3) {
        fprintf(stderr, "usage: %s <graph.osm.pbf> <flood_depth.txt> [passable_depth_m]\n", argv[0]);
        return 1;
    }
    const char* pbf = argv[1];
    const char* raster = argv[2];
    double thr = argc > 3 ? atof(argv[3]) : 0.5;
    const unsigned IMPASS = 1000000000u;

    // Load the OSM car graph via the lower-level loader (not
    // simple_load_osm_car_routing_graph_from_pbf) so the way callback can
    // capture each way's name tag alongside speed and direction.
    auto mapping = load_osm_id_mapping_from_pbf(pbf, nullptr,
        [&](uint64_t wid, const TagMap& tags) { return is_osm_way_used_by_cars(wid, tags, nullptr); },
        nullptr, false);
    unsigned rwc = mapping.is_routing_way.population_count();
    std::vector<unsigned> way_speed(rwc);
    std::vector<std::string> way_name(rwc);
    auto graph = load_osm_routing_graph_from_pbf(pbf, mapping,
        [&](uint64_t wid, unsigned rwid, const TagMap& tags) {
            way_speed[rwid] = get_osm_way_speed(wid, tags, nullptr);
            const char* nm = tags["name"]; if (nm) way_name[rwid] = nm;
            return get_osm_car_direction_category(wid, tags, nullptr);
        },
        [&](uint64_t rid, const std::vector<OSMRelationMember>& m, const TagMap& tags,
            std::function<void(OSMTurnRestriction)> cb) {
            return decode_osm_car_turn_restrictions(rid, m, tags, cb, nullptr);
        }, nullptr);
    mapping = OSMRoutingIDMapping();

    unsigned n = graph.node_count(), A = graph.head.size();
    auto tail = invert_inverse_vector(graph.first_out);
    auto& lat = graph.latitude; auto& lon = graph.longitude;

    long t0 = get_micro_time();
    auto order = compute_nested_node_dissection_order_using_inertial_flow(n, tail, graph.head, lat, lon);
    CustomizableContractionHierarchy cch(order, tail, graph.head);
    double pre_ms = (get_micro_time() - t0) / 1000.0;

    // Read vkflood's raster: a '# bbox lat A..B lon C..D' header, then a DxD
    // depth grid (metres). Depth is sampled onto each arc's head-node
    // position, so routing happens on the street graph, not the raster grid.
    int D = 0; double la0 = 0, la1 = 0, lo0 = 0, lo1 = 0;
    std::vector<std::vector<double>> grid;
    { std::ifstream f(raster); std::string line;
      while (std::getline(f, line)) {
        if (line.empty()) continue;
        if (line[0] == '#') {
            if (line.find("bbox") != std::string::npos)
                std::sscanf(line.c_str(), "# bbox lat %lf..%lf lon %lf..%lf", &la0, &la1, &lo0, &lo1);
            continue;
        }
        std::vector<double> row; std::istringstream ss(line); double v;
        while (ss >> v) row.push_back(v);
        if (!row.empty()) grid.push_back(row);
      }
      D = grid.size();
    }
    auto depth_at = [&](double la, double lo) -> double {
        if (D == 0 || la < la0 || la > la1 || lo < lo0 || lo > lo1) return 0.0;
        int r = (int)((la1 - la) / (la1 - la0) * D); if (r < 0) r = 0; if (r >= D) r = D - 1;
        int c = (int)((lo - lo0) / (lo1 - lo0) * D); if (c < 0) c = 0; if (c >= (int)grid[r].size()) c = grid[r].size() - 1;
        return grid[r][c];
    };

    std::vector<unsigned> w_base(A), w_flood(A);
    long impass = 0;
    for (unsigned a = 0; a < A; a++) {
        unsigned base = graph.geo_distance[a]; w_base[a] = base;
        double d = depth_at(lat[graph.head[a]], lon[graph.head[a]]);
        if (d > thr) { w_flood[a] = base + IMPASS; impass++; } else w_flood[a] = base;
    }

    // Source/target straddle the flood bbox (west/east of it) so a real
    // detour around the flooded area exists rather than a total barrier.
    double midlat = (la0 + la1) / 2, w_lon = lo1 - lo0;
    auto nearest = [&](double la, double lo) -> unsigned {
        unsigned best = 0; double bd = 1e18;
        for (unsigned i = 0; i < n; i++) { double dl = lat[i] - la, dg = lon[i] - lo, d = dl * dl + dg * dg; if (d < bd) { bd = d; best = i; } }
        return best;
    };
    unsigned s = nearest(midlat, lo0 - w_lon * 0.4), t = nearest(midlat, lo1 + w_lon * 0.4);

    CustomizableContractionHierarchyMetric mb(cch, w_base); mb.customize();
    CustomizableContractionHierarchyQuery qb(mb); qb.reset().add_source(s).add_target(t).run();
    unsigned base_dist = qb.get_distance();

    long c0 = get_micro_time();
    CustomizableContractionHierarchyMetric mf(cch, w_flood); mf.customize();
    double custom_ms = (get_micro_time() - c0) / 1000.0;
    CustomizableContractionHierarchyQuery qf(mf); qf.reset().add_source(s).add_target(t).run();
    unsigned flood_dist = qf.get_distance();
    bool stranded = (flood_dist >= IMPASS);

    printf("graph: nodes=%u arcs=%u  CCH_preprocess_ms=%.0f\n", n, A, pre_ms);
    printf("flood: threshold=%.2f m  impassable_arcs=%ld/%u  recustomize_ms=%.1f\n", thr, impass, A, custom_ms);
    printf("baseline_no_flood_m=%u\n", base_dist);
    if (stranded) { printf("flood_aware: STRANDED\n"); return 0; }
    printf("flood_aware_m=%u  detour_extra_m=%d\n", flood_dist, (int)flood_dist - (int)base_dist);

    auto arcs = qf.get_arc_path();
    std::string prev;
    printf("route_streets:");
    for (unsigned a : arcs) {
        std::string nm = way_name[graph.way[a]];
        if (nm.empty()) nm = "(unnamed road)";
        if (nm != prev) { printf(" > %s", nm.c_str()); prev = nm; }
    }
    printf("\n");
    return 0;
}
