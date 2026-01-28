from owlready2 import * # type: ignore
import re
import json
from enum import Enum
# import graphviz

class Graphs(Enum):
    Mermaid = "mermaid"
    VisJs = "visjs"
    #GraphViz = "graphviz"

def safe_id(text):
    """Sanitizes strings for Mermaid Node IDs (alphanumeric only)."""
    return re.sub(r'[\W_]+', '', str(text))

def label(x):
    """Robust labeling."""
    if hasattr(x, "label") and x.label: return x.label[0]
    if hasattr(x, "name"): return x.name
    return str(x)

def comment(x):
    return str(x.comment[0]) if hasattr(x, "comment") and x.comment else ""

def generate_class_hierarchy_mermaid(classes,prefix):
    lines = ["graph TD"]
    lines.append('    %%{init: {"flowchart": {"padding": 20, "nodeSpacing": 50, "rankSpacing": 50}}}%%')
    lines.append('    classDef classNode fill:#ff6b35,stroke:#e55a2b,stroke-width:2px,color:#fff')
    lines.append('    classDef rootNode fill:#f7931e,stroke:#e55a2b,stroke-width:2px,color:#fff')
    
    lines.append('    Thing["owl:Thing"]:::rootNode')
    
    processed = set()
    
    def add_node(cls):
        if cls in processed: return
        processed.add(cls)
        
        node_id = safe_id(cls.name)
        lines.append(f'    {node_id}["{label(cls)}"]:::classNode')
        
        lines.append(f'    click {node_id} "entities/{node_id}.html" "Go to {label(cls)}"')

        parents = [p for p in cls.is_a if isinstance(p, ThingClass) and prefix in p.iri]
        if not parents:
             lines.append(f'    Thing --> {node_id}')
        else:
            for p in parents:
                p_id = safe_id(p.name)
                lines.append(f'    {p_id} --> {node_id}')
                add_node(p) 

    for c in classes:
        add_node(c)
        
    return "\n".join(lines)

def generate_property_graph_mermaid(classes, properties,prefix):
    lines = ["graph BT"]
    
    lines.append('    %%{init: {"flowchart": {"nodeSpacing": 80, "rankSpacing": 100}}}%%')
    
    lines.append('    classDef classNode fill:#ff6b35,stroke:#e55a2b,stroke-width:2px,color:#fff,font-weight:bold')

    added_rels = set()
    active_nodes = set()
    
    rels_to_draw = []
    
    for cls in classes:
        for condition in cls.is_a:
            if isinstance(condition, Restriction):
                prop = condition.property
                target = condition.value
                if isinstance(target, ThingClass) and prefix in target.iri:
                    rels_to_draw.append((cls, target, prop))

    for prop in properties:
        domains = [d for d in prop.domain if isinstance(d, ThingClass) and prefix in d.iri]
        ranges = [r for r in prop.range if isinstance(r, ThingClass) and prefix in r.iri]
        for d in domains:
            for r in ranges:
                rels_to_draw.append((d, r, prop))

    for s, o, p in rels_to_draw:
        key = (s, o, p)
        if key not in added_rels:
            s_id = safe_id(s.name)
            o_id = safe_id(o.name)
            p_lbl = label(p)
            
            lines.append(f'    {s_id} -- "{p_lbl}" --> {o_id}')
            
            active_nodes.add(s)
            active_nodes.add(o)
            added_rels.add(key)

    for node in active_nodes:
        n_id = safe_id(node.name)
        lines.append(f'    {n_id}["{label(node)}"]:::classNode')
        lines.append(f'    click {n_id} "entities/{n_id}.html"')

    if len(lines) == 3:
        lines.append('    NoRelations["No properties found"]:::classNode')

    return "\n".join(lines)

def generate_instance_network_mermaid(individuals, properties):
    lines = ["graph LR"]
    
    lines.append('    %%{init: {"flowchart": {"nodeSpacing": 50, "rankSpacing": 80, "curve": "basis"}}}%%')
    
    lines.append('    classDef instanceNode fill:#ff6b35,stroke:#e55a2b,stroke-width:2px,color:#fff')
    
    active_inds = set()
    edges_to_draw = []

    for prop in properties:
        for s, o in prop.get_relations():
            if s in individuals and o in individuals:
                edges_to_draw.append((s, prop, o))
                active_inds.add(s)
                active_inds.add(o)

    for ind in sorted(list(active_inds), key=lambda x: x.name):
        ind_id = safe_id(ind.name)
        lines.append(f'    {ind_id}["{label(ind)}"]:::instanceNode')
        lines.append(f'    click {ind_id} "entities/{ind_id}.html"')

    edges_to_draw.sort(key=lambda x: (x[0].name, x[1].name, x[2].name))
    
    link_counter = 0
    link_styles = []

    for s, prop, o in edges_to_draw:
        s_id = safe_id(s.name)
        o_id = safe_id(o.name)
        p_lbl = label(prop)
        p_name_lower = prop.name.lower()
        
        lines.append(f'    {s_id} -- "{p_lbl}" --> {o_id}')
        
        style = "stroke:#999,stroke-width:1px"
        
        if "negatively" in p_name_lower:
            style = "stroke:#dc3545,stroke-width:2px" 
        elif "positively" in p_name_lower:
            style = "stroke:#28a745,stroke-width:2px" 
        elif "refines" in p_name_lower:
            style = "stroke:#007bff,stroke-width:1px,stroke-dasharray: 5 5" 
        elif "evaluates" in p_name_lower:
            style = "stroke:#6f42c1,stroke-width:2px" 
        elif "ismeasuredby" in p_name_lower:
            style = "stroke:#e83e8c,stroke-width:2px" 
        elif "validfor" in p_name_lower:
            style = "stroke:#fd7e14,stroke-width:2px,stroke-dasharray: 3 3" 
        
        link_styles.append(f'    linkStyle {link_counter} {style};')
        link_counter += 1

    lines.extend(link_styles)

    if not active_inds:
        lines.append('    Empty["No connected instances found"]')

    return "\n".join(lines)

def generate_instance_network_visjs(individuals, properties):
    nodes = []
    edges = []
    added_nodes = set()
    
    for prop in properties:
        for s, o in prop.get_relations():
            if s in individuals and o in individuals:
                
                if s not in added_nodes:
                    group = "Default"
                    if s.is_a:
                        group = s.is_a[0].name 
                    
                    nodes.append({
                        "id": safe_id(s.name),
                        "label": label(s),
                        "group": group,
                        "title": f"{label(s)} ({group})"
                    })
                    added_nodes.add(s)
                
                if o not in added_nodes:
                    group = "Default"
                    if o.is_a:
                        group = o.is_a[0].name
                        
                    nodes.append({
                        "id": safe_id(o.name),
                        "label": label(o),
                        "group": group,
                        "title": f"{label(o)} ({group})"
                    })
                    added_nodes.add(o)

                color = "#848484" 
                width = 1
                dashes = False
                
                p_name = prop.name.lower()
                
                if "negatively" in p_name: 
                    color = "#dc3545" 
                    width = 2
                elif "positively" in p_name: 
                    color = "#28a745" 
                    width = 2
                elif "ismeasuredby" in p_name: 
                    color = "#e83e8c" 
                    width = 2
                elif "evaluates" in p_name:
                    color = "#6f42c1" 
                elif "refines" in p_name:
                    color = "#007bff" 
                    dashes = True 
                
                edges.append({
                    "from": safe_id(s.name),
                    "to": safe_id(o.name),
                    "label": label(prop),
                    "color": {"color": color},
                    "width": width,
                    "dashes": dashes,
                    "arrows": "to",
                    "font": {"align": "middle", "size": 10} 
                })
                
    return json.dumps({"nodes": nodes, "edges": edges})

# def generate_instance_network_graphviz(individuals, properties):
    # """
    # Génère un graphe SVG statique ARBORESCENT (Hiérarchique).
    # Utilise le moteur 'dot' au lieu de 'neato'.
    # """
    # dot = graphviz.Digraph(comment='Instance Network', format='svg', engine='dot')
    
    # dot.attr(rankdir='LR')        
    
    # dot.attr(splines='polyline')  
    
    # dot.attr(nodesep='0.4')       
    # dot.attr(ranksep='1.5')       
    # dot.attr(concentrate='true')  
    
    # dot.attr('node', shape='box', style='filled,rounded', fontname='Helvetica', fontsize='12', margin='0.2,0.1')
    # dot.attr('edge', fontsize='10', fontname='Helvetica')

    # added_nodes = set()
    
    # for prop in properties:
    #     for s, o in prop.get_relations():
    #         if s in individuals and o in individuals:
                
    #             if s not in added_nodes:
    #                 fill = "#d3d3d3"
    #                 if s.is_a:
    #                     p_name = s.is_a[0].name
    #                     if "Criteria" in p_name: fill = "#ff6b35"
    #                     elif "Metric" in p_name: fill = "#20c997"
    #                     elif "Fairness" in p_name: fill = "#6f42c1"
                    
    #                 dot.node(safe_id(s.name), label(s), 
    #                          fillcolor=fill, color=fill, fontcolor='white',
    #                          URL=f"entities/{safe_id(s.name)}.html")
    #                 added_nodes.add(s)
                
    #             if o not in added_nodes:
    #                 fill = "#d3d3d3"
    #                 if o.is_a:
    #                     p_name = o.is_a[0].name
    #                     if "Criteria" in p_name: fill = "#ff6b35"
    #                     elif "Metric" in p_name: fill = "#20c997"
    #                     elif "Fairness" in p_name: fill = "#6f42c1"

    #                 dot.node(safe_id(o.name), label(o), 
    #                          fillcolor=fill, color=fill, fontcolor='white',
    #                          URL=f"entities/{safe_id(o.name)}.html")
    #                 added_nodes.add(o)

    #             color = "#999999"
    #             p_name = prop.name.lower()
    #             penwidth = "1"
    #             style = "solid"
                
    #             if "positively" in p_name: color = "#28a745"; penwidth="2"
    #             elif "negatively" in p_name: color = "#dc3545"; penwidth="2"
    #             elif "ismeasuredby" in p_name: 
    #                 color = "#e83e8c" 
    #                 penwidth="2"
    #             elif "refines" in p_name: style = "dashed"

    #             dot.edge(safe_id(s.name), safe_id(o.name), 
    #                      label=label(prop), 
    #                      color=color, fontcolor="#555555", 
    #                      penwidth=penwidth, style=style)

    # return dot.pipe().decode('utf-8').replace('width="', 'data-width="').replace('height="', 'data-height="')