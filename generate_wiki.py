import owlready2 # type: ignore
import jinja2
import os
import sys
import argparse
from graph import *


parser=argparse.ArgumentParser(prog='OntoViz')

parser.add_argument("onto_path", help="Path to the ontology file")
parser.add_argument("-o","--output", default="wiki", help="Output directory of the wiki. (default=wiki)")
parser.add_argument("-g","--graph",
                    choices=[member.value for member in Graphs],
                    default=Graphs.Mermaid.value,
                    help="Instance graph visualization method. (default=mermaid)")

args = parser.parse_args()

ONTOLOGY_PATH = args.onto_path
OUTPUT = args.output
GRAPH = Graphs(args.graph)
CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

try:
    onto = get_ontology(ONTOLOGY_PATH).load() # type: ignore
except FileNotFoundError:
    print(f"Error: Could not find {ONTOLOGY_PATH}.")
    exit(1)

PREFIX = onto.base_iri
try:
    NAME = onto.metadata.label[0]
except Exception as e:
    print("Error loading the ontology label, fallbacking to default name :\"Ontology Visualizer\"")
    NAME = "Ontology visualiser"

env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(CURRENT_DIRECTORY,"templates")))
try:
    index_template = env.get_template("index.html")
    entity_template = env.get_template("entity.html")
    class_template = env.get_template("class.html")
    property_template = env.get_template("property.html")
    viz_template = env.get_template("visualizations.html")
    network_template = env.get_template(f"network_{GRAPH.value}.html")
    
except jinja2.TemplateNotFound as e:
    print(f"Could not find template file: {e.name}")
    exit(1)
except jinja2.TemplateSyntaxError as e:
    print(f"Syntax error in template file: {e.filename} at line {e.message}")
    exit(1)
except Exception as e:
    import traceback
    traceback.print_exc()
    exit(1)

os.makedirs(f"{OUTPUT}/entities", exist_ok=True)
os.makedirs(f"{OUTPUT}/static", exist_ok=True)
if os.path.exists(os.path.join(CURRENT_DIRECTORY,"static/style.css")):
    os.system(f"cp {CURRENT_DIRECTORY}/static/style.css {OUTPUT}/static/style.css")

def write_entity_page(entity, template):
    """Writes individual HTML pages for entities."""
    fname = f"{safe_id(label(entity))}.html"
    
    html = template.render(
        label=label(entity),
        uri=entity.iri,
        comment=comment(entity),
        types=[label(t) for t in entity.is_a if not isinstance(t, (owlready2.Restriction,owlready2.Or,owlready2.And))],
        relations=rels[entity],
        anti_rels=anti[entity],
        data_rels=data_rels[entity],
        individuals= class_dic[entity] if entity in classes else (prop_dic[entity] if entity in object_properties else [])
    )
    with open(f"{OUTPUT}/entities/{fname}", "w", encoding="utf-8") as f:
        f.write(html)
    return fname


classes = [c for c in onto.classes() if PREFIX in c.iri]
object_properties = [p for p in onto.object_properties() if PREFIX in p.iri]
data_properties = [p for p in onto.data_properties() if PREFIX in p.iri]
individuals = [i for i in onto.individuals() if PREFIX in i.iri]

class_dic = {c: [label(i) for i in c.instances() if i.iri.startswith(PREFIX)] for c in classes}

rels = {ent: [] for ent in classes + object_properties + data_properties + individuals}
data_rels = {ent: [] for ent in classes + object_properties + data_properties + individuals}
anti = {ent: [] for ent in classes + object_properties + data_properties + individuals}
prop_dic = {p: [] for p in object_properties + data_properties}

for prop in object_properties:
    for s, o in prop.get_relations():
        prop_dic[prop].append((label(s), label(o)))
        rels[s].append((label(prop), label(o)))
        anti[o].append((label(s), label(prop)))


for prop in data_properties:
    for s, o in prop.get_relations():
        prop_dic[prop].append((label(s), label(o)))
        data_rels[s].append((label(prop), label(o)))

for c in classes:
    write_entity_page(c, class_template)
    
for p in object_properties + data_properties:
    write_entity_page(p, property_template)
    
for i in individuals:
    write_entity_page(i, entity_template)


viz_html = viz_template.render(
    class_hierarchy=generate_class_hierarchy_mermaid(classes,PREFIX),
    property_graph=generate_property_graph_mermaid(classes, object_properties,PREFIX)
)

with open(f"{OUTPUT}/visualizations.html", "w", encoding="utf-8") as f:
    f.write(viz_html)

match GRAPH:
    case Graphs.Mermaid:
        viz_network = network_template.render(
            instance_network=generate_instance_network_mermaid(individuals, object_properties))
    
    case Graphs.VisJs:
        viz_network = network_template.render(
            instance_network=generate_instance_network_visjs(individuals, object_properties))
    
    # case Graphs.GraphViz:
    #     viz_network = network_graphviz_template.render(
    #         instance_network=generate_instance_network_graphviz(individuals, properties))

with open(f"{OUTPUT}/network.html", "w", encoding="utf-8") as f:
    f.write(viz_network)

index_html = index_template.render(
    title=NAME,
    classes=[{"label": label(c), "file": f"{safe_id(label(c))}.html"} for c in classes],
    properties=[{"label": label(p), "file": f"{safe_id(label(p))}.html"} for p in object_properties],
    individuals=[{"label": label(i), "file": f"{safe_id(label(i))}.html"} for i in individuals]
)
with open(f"{OUTPUT}/index.html", "w", encoding="utf-8") as f:
    f.write(index_html)
