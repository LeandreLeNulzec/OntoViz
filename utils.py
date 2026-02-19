import owlready2 # type: ignore
import jinja2
import re

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

def load_ontology(path):
    try:
        ontology = owlready2.get_ontology(path).load() # type: ignore
    except FileNotFoundError:
        print(f"Error: Could not find {path}.")
        exit(1)
    return ontology

def load_templates(env,graph_type):
    try:
        index_template = env.get_template("index.html")
        entity_template = env.get_template("entity.html")
        class_template = env.get_template("class.html")
        property_template = env.get_template("property.html")
        viz_template = env.get_template("visualizations.html")
        network_template = env.get_template(f"network_{graph_type}.html")
        
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
    return [index_template,entity_template,class_template,property_template,viz_template,network_template]

def write_entity_page(entity, template, relations, antirelations, data_relations, class_dictionary, classes, properties_dictionnary, object_properties, OUTPUT):
    """Writes individual HTML pages for entities."""
    fname = f"{safe_id(label(entity))}.html"
    
    html = template.render(
        label=label(entity),
        uri=entity.iri,
        comment=comment(entity),
        types=[label(t) for t in entity.is_a if not isinstance(t, (owlready2.Restriction,owlready2.Or,owlready2.And))],
        relations=relations[entity],
        anti_rels=antirelations[entity],
        data_rels=data_relations[entity],
        individuals= class_dictionary[entity] if entity in classes else (properties_dictionnary[entity] if entity in object_properties else [])
    )
    with open(f"{OUTPUT}/entities/{fname}", "w", encoding="utf-8") as f:
        f.write(html)
    return fname