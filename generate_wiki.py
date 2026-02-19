import owlready2 # type: ignore
import jinja2
import os
import sys
import rdflib # type: ignore
import argparse
from graph import *
from utils import *


parser=argparse.ArgumentParser(prog='OntoViz')

parser.add_argument("onto_path", help="Path to the ontology file")
parser.add_argument("-n","--name",default="Ontology Visualiser", help="The name to give to the generated visualier")
parser.add_argument("-o","--output", default="wiki", help="Output directory of the wiki. (default=wiki)")
parser.add_argument("-g","--graph",
                    choices=[member.value for member in Graphs],
                    default=Graphs.Mermaid.value,
                    help="Instance graph visualization method. (default=mermaid)")

args = parser.parse_args()

NAME = args.name
MAIN_PATH = args.onto_path
OUTPUT = args.output
GRAPH = Graphs(args.graph)
CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

if MAIN_PATH.endswith(".ttl"):
    g = rdflib.Graph()
    g.parse(MAIN_PATH, format="turtle")
    g.serialize(destination=(MAIN_PATH[:-4] + ".rdf"), format="xml")
    MAIN_PATH = MAIN_PATH[:-4] + ".rdf"

main_onto = load_ontology(MAIN_PATH)

PREFIX = main_onto.base_iri
try:
    NAME = main_onto.metadata.label[0]
except Exception as e:
    print("Error loading the ontology label, fallbacking to default name :\"Ontology Visualizer\"")
    NAME = "Ontology visualiser"

env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(CURRENT_DIRECTORY,"templates")))
[index_template,entity_template,class_template,property_template,viz_template,network_template] = load_templates(env,f"{GRAPH.value}")

os.makedirs(f"{OUTPUT}/entities", exist_ok=True)
os.makedirs(f"{OUTPUT}/static", exist_ok=True)
if os.path.exists(os.path.join(CURRENT_DIRECTORY,"static/style.css")):
    os.system(f"cp {CURRENT_DIRECTORY}/static/style.css {OUTPUT}/static/style.css")


classes = [c for c in main_onto.classes()]
object_properties = [p for p in main_onto.object_properties()]
data_properties = [p for p in main_onto.data_properties()]
individuals = []
for c in classes:
    for i in c.instances():
        individuals.append(i)


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
    write_entity_page(c, class_template, rels, anti, data_rels, class_dic, classes, prop_dic, object_properties,OUTPUT)
    
for p in object_properties + data_properties:
    write_entity_page(p, property_template, rels, anti, data_rels, class_dic, classes, prop_dic, object_properties,OUTPUT)
    
for i in individuals:
    write_entity_page(i, entity_template, rels, anti, data_rels, class_dic, classes, prop_dic, object_properties,OUTPUT)


viz_html = viz_template.render(
    class_hierarchy=generate_class_hierarchy_mermaid(classes,PREFIX),
    property_graph=generate_property_graph_mermaid(classes,object_properties,PREFIX)
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
