# OntoViz

**OntoViz** is a static site generator designed to transform ontologies into interactive, navigable web "wikis". It bridges the gap between complex semantic data and human-readable documentation by providing structured browsing and dynamic visualizations.

## Key Features

* **Semantic Wiki Generation:** Automatically creates a cross-linked HTML browser for your ontology.
* **Entity Browsing:** Dedicated, detailed pages for every **Class**, **Property**, and **Individual** (instance).
* **Interactive Visualizations:**
    * **Class Hierarchy:** A zoomable, clickable taxonomy of your classes powered by Mermaid.js.
    * **Property Relationships:** A graph visualizing how concepts are linked via object properties.
* **Advanced Instance Networking:** Map out all individuals and their relationships using multiple rendering engines
* **Relationship Tracking:** Clearly displays direct and inverse relations for every entity.

## Technical Stack

* **Pytohn:** Python 3.10+.
* **Ontology Engine:** [Owlready2](https://owlready2.readthedocs.io/).
* **HTML Templating:** [Jinja2](https://jinja.palletsprojects.com/).
* **Frontend Libraries:**
    * [Mermaid.js](https://mermaid.js.org/) (Diagrams).
    * [Vis-Network](https://visjs.org/) (Interactive Graphs).
    * [svg-pan-zoom](https://github.com/ariutta/svg-pan-zoom) (Navigation).

## Dependencies
Install the required Python libraries:
```bash
pip install owlready2 jinja2
```

## Usage

The generator is tested exclusively using RDF/XML files, I don't know how it might behave for other format suported by owlready2.
Run the generator using the `generate_wiki.py` script:

```bash
python generate_wiki.py <path_to_ontology_file> [options]
```

### Options:
* `onto_path`: **(Required)** Path to your ontology file (e.g., `example.rdf`).
* `-o`, `--output`: Set the output directory for the wiki files (default: `wiki`).
* `-g`, `--graph`: Select the instance network engine. Choices: `mermaid` (default) or `visjs`.

## Generative AI Disclosure
This project was developed with the assistance of Generative AI. I used it to:
* Help my learning process regarding RDF structures.
* Help me choose the technology (owlready2, jinja2, Mermaid.js, Vis.js, ) and give me simple examples/tutorials/documentation.
* Write the jinja2 templates and the css style.
* Draft project documentation.

## Project Status: Experimental
This project is an **experimental learning endeavor**. As I still have a poor understanding of ontology, the tool may have limitations or flaws in how it interprets or displays semantic relationships. Feedback and contributions are encouraged and appreciated !

## License
This project is licensed under the **MIT License**. See the `LICENSE` file for details.