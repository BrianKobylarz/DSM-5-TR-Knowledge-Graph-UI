DSM-5-TR-Knowledge-Graph-UI
Description
This Python script generates an interactive network (knowledge graph) visualization of mental disorders and their symptoms, organized according to DSM-5-TR diagnostic categories. It reads relationship data (symptoms, comorbidities) from a CSV file and produces an HTML file containing the interactive graph, various analysis tools, and filtering options.

Features
Interactive Network Graph: Visualizes disorders (dots) and symptoms (triangles) connected by their relationships.
DSM-5-TR Categorization: Nodes are colored based on their primary DSM category.
Relationship Types: Edges represent "HAS_SYMPTOM" (Disorder -> Symptom, Blue Arrow) or "COMORBID_WITH" (Disorder <-> Disorder, Red Bidirectional Arrow) relationships.
Rich UI Controls (in HTML output):
Network Overview: Displays basic network metrics (visible nodes/edges).
Node/Edge Creation: Dynamically add new disorders or symptoms and define relationships between them.
Network Analysis Tools: Simulate network disruptions by removing nodes (highest degree, random, selected) or edges (random percentage, central percentage approximation, selected).
Restore Network: Revert any node/edge removals.
Search & Navigation: Search for specific disorders, isolate selected disorders and their connections, freeze/unfreeze the layout.
Category Filtering: An interactive legend allows filtering the view to show only nodes and edges related to a selected DSM category.
Data Cleaning: Automatically removes the "SYM_" prefix from symptom names for better readability.
Console Output: Prints network statistics (node/edge counts, category breakdowns) to the console upon execution.
Requirements
Python 3.x
Python Libraries: Install the required libraries using pip:
pip install pandas networkx pyvis matplotlib
Input Data File: A CSV file named merged_disorders_data.csv must be present in the same directory as the script.
Data Format (merged_disorders_data.csv)
The script expects the input CSV file (merged_disorders_data.csv) to contain columns representing the relationships between entities (disorders and symptoms). Key expected columns include:

source_name: The name of the source node (e.g., a disorder).
target_name: The name of the target node (e.g., a symptom or another disorder). Symptoms might have a SYM_ prefix in the data, which the script will remove for display.
relationship_type: The type of link (e.g., HAS_SYMPTOM, COMORBID_WITH).
source_category: The DSM category of the source node.
target_category: The DSM category of the target node.
source_type: The type of the source node (e.g., Disorder).
target_type: The type of the target node (e.g., Symptom or Disorder).
Note: Ensure category columns are consistently formatted.

Usage
Install Requirements: Make sure Python and the required libraries (pandas, networkx, pyvis, matplotlib) are installed.
Prepare Data: Place your correctly formatted merged_disorders_data.csv file in the same directory as the DSM-5-TR Visualizer.py script.
Run the Script: Execute the script from your terminal:
python "DSM-5-TR Visualizer.py"
View Output:
The script will print network statistics to the console.
It will generate an HTML file named network_with_categories.html in the same directory.
The script will attempt to automatically open this HTML file in your default web browser. If this fails, manually open the network_with_categories.html file.
Interactivity Guide (HTML Output)
The generated network_with_categories.html file provides several interactive elements:

Main Network Pane:
Drag nodes to rearrange the layout (if not frozen).
Hover over nodes/edges to see tooltips (Category, Relationship Type).
Click on nodes/edges to select them (used for removal tools). Use Ctrl+Click or Shift+Click for multi-select.
Zoom and pan using mouse controls or navigation buttons (if enabled in pyvis options).
Left Control Panel:
Network Overview: Shows counts of currently visible nodes and edges.
Node/Edge Creation: Toggle modes to add nodes (click on empty space) or edges (click source node, then target node). Use dropdowns to select type/category.
Network Analysis Tools: Buttons to remove nodes/edges based on different criteria. Restore Network brings back all removed elements.
Search & Navigation: Search for disorders, isolate up to 3 disorders (comma-separated), and freeze/unfreeze the physics simulation.
Floating Legend (Top-Left): Explains the shapes and colors used for disorders, symptoms, and relationship types.
Right Legend Panel:
Lists all DSM categories found in the data, along with counts.
Click a category name to filter the network, showing only disorders in that category and their direct connections (symptoms, comorbid disorders).
Click the Show All Categories button to reset the view.
Contributing
Contributions or suggestions for improvement are welcome. Please feel free to open an issue or submit a pull request if you identify bugs or have ideas for new features.

License
MIT License

Copyright (c) 2025 Brian Kobylarz

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.