# Network Visualization for DSM-5-TR Categories
# This script creates an interactive network visualization of mental disorders
# and their symptoms, organized by DSM-5-TR categories.

import json
import os
import webbrowser
from collections import defaultdict

import matplotlib.colors as mcolors
import networkx as nx
import pandas as pd
from pyvis.network import Network


def create_dsm_color_palette(categories):
    """
    Create a consistent color mapping for DSM categories.
    Uses a combination of distinctive colors to ensure each category is visually distinct.
    """
    base_colors = list(mcolors.TABLEAU_COLORS.values())
    extended_colors = [
        '#8B4513',  # Saddle Brown
        '#4B0082',  # Indigo
        '#800000',  # Maroon
        '#006400',  # Dark Green
        '#483D8B',  # Dark Slate Blue
        '#8B008B',  # Dark Magenta
        '#2F4F4F',  # Dark Slate Gray
        '#8B4513',  # Saddle Brown (duplicate, but okay for cycling)
        '#000080'  # Navy
    ]
    all_colors = base_colors + extended_colors

    # Create a deterministic mapping of categories to colors
    categories = sorted(list(set(categories)))  # Sort for consistency
    return {cat: all_colors[i % len(all_colors)] for i, cat in enumerate(categories)}


def create_complete_graph(disorders_df, relationships_df, categories_df):
    """
    Create a graph showing all disorders and their relationships, organized by DSM categories.
    Removes SYM_ prefix from symptom names and assigns bipartite (0=disorder, 1=symptom).
    """
    G = nx.Graph()

    # Create dictionaries to track node information
    node_info = {}

    # First pass: collect all node information and clean symptom names
    for _, row in categories_df.iterrows():
        # Process source node (usually a disorder)
        node_info[row['source_name']] = {
            'type': row['source_type'],
            'category': row['source_category']
        }

        # Process target node (could be symptom or disorder)
        target_name = row['target_name']
        if row['target_type'].lower() == 'symptom' and target_name.startswith('SYM_'):
            target_name = target_name[4:]  # Remove 'SYM_' prefix

        node_info[target_name] = {
            'type': row['target_type'],
            'category': row['target_category']
        }

    # Add nodes with proper categorization
    for node_name, info in node_info.items():
        is_symptom = info['type'].lower() == 'symptom'
        G.add_node(node_name,
                   bipartite=1 if is_symptom else 0,
                   category=info['category'],
                   node_type=info['type'])

    # Add edges with cleaned symptom names
    for _, row in categories_df.iterrows():
        target_name = row['target_name']
        if row['target_type'].lower() == 'symptom' and target_name.startswith('SYM_'):
            target_name = target_name[4:]

        if row['relationship_type'] == 'HAS_SYMPTOM':
            G.add_edge(row['source_name'], target_name, relationship='HAS_SYMPTOM')
        elif row['relationship_type'] == 'COMORBID_WITH':
            G.add_edge(row['source_name'], target_name, relationship='COMORBID_WITH')

    return G


def get_category_info(G):
    """
    Get detailed information about each DSM category for the legend.
    """
    category_info = defaultdict(lambda: {'disorders': [], 'symptoms': [], 'count': 0})

    for node, attrs in G.nodes(data=True):
        category = attrs.get('category', 'Uncategorized')
        is_symptom = attrs.get('node_type', '').lower() == 'symptom'
        node_list = 'symptoms' if is_symptom else 'disorders'
        category_info[category][node_list].append(node)
        category_info[category]['count'] += 1

    return category_info


def calculate_network_metrics(G):
    """
    Calculate comprehensive network metrics including category-specific analysis.
    """
    metrics = {
        'node_count': G.number_of_nodes(),
        'edge_count': G.number_of_edges(),
        'avg_degree': sum(dict(G.degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0,
        'density': nx.density(G),
        'clustering_coefficient': nx.average_clustering(G),
        'connected_components': len(list(nx.connected_components(G))) if G.number_of_nodes() > 0 else 0,
        'largest_component_size': len(max(nx.connected_components(G), key=len)) if G.number_of_nodes() > 0 else 0
    }

    # Calculate category-specific metrics
    category_metrics = defaultdict(lambda: {'disorders': 0, 'symptoms': 0, 'internal_edges': 0})
    for node, attrs in G.nodes(data=True):
        category = attrs.get('category', 'Uncategorized')
        is_disorder = attrs.get('bipartite') == 0
        category_metrics[category]['disorders' if is_disorder else 'symptoms'] += 1

    # Count internal edges within categories
    for edge in G.edges():
        cat1 = G.nodes[edge[0]].get('category', 'Uncategorized')
        cat2 = G.nodes[edge[1]].get('category', 'Uncategorized')
        if cat1 == cat2:
            category_metrics[cat1]['internal_edges'] += 1

    metrics['category_metrics'] = dict(category_metrics)

    # Compute average shortest path length for connected components
    if nx.is_connected(G) and G.number_of_nodes() > 1:
        largest_cc = max(nx.connected_components(G), key=len)
        subG = G.subgraph(largest_cc)
        metrics['avg_shortest_path'] = nx.average_shortest_path_length(subG)
    else:
        metrics['avg_shortest_path'] = float('inf')

    return metrics


def visualize_graph(G, html_file='disorder_network.html', print_analysis=True):
    """
    Create an interactive visualization of the disorder network with DSM categories.
    """
    # Get category information and node attributes
    category_info = get_category_info(G)
    node_attrs = nx.get_node_attributes(G, 'bipartite')

    # Create color mapping for categories
    categories = {data['category'] for _, data in G.nodes(data=True)}
    category_colors = create_dsm_color_palette(categories)

    # Initialize network
    net = Network(height='1000px', width='100%', bgcolor='#ffffff', font_color='#000000')
    node_data = {}
    edge_data = {}

    # Node styling
    for node, attrs in G.nodes(data=True):
        is_disorder = attrs.get('bipartite') == 0
        category = attrs.get('category', 'Uncategorized')
        color = category_colors[category]

        node_data[node] = {
            'id': node,
            'label': node,
            'color': color,
            'originalColor': color,
            'category': category,
            'size': 80 if is_disorder else 75,
            'shape': 'dot' if is_disorder else 'triangle',
            'borderWidth': 0,
            'borderColor': '#2B7CE9' if is_disorder else '#008000',
            'hidden': False,
            'title': f"Category: {category}"
        }

    # Add nodes
    for node, properties in node_data.items():
        net.add_node(
            node,
            label=properties['label'],
            color={
                'background': properties['color'],
                'border': properties['borderColor']
            },
            size=properties['size'],
            shape=properties['shape'],
            borderWidth=properties['borderWidth'],
            title=properties['title'],
            hidden=properties['hidden'],
            category=properties['category']
        )

    # Edge styles
    edge_types = {
        'HAS_SYMPTOM': {
            'color': '#0000FF',
            'width': 1,
            'arrows': 'to'
        },
        'COMORBID_WITH': {
            'color': '#FF0000',
            'width': 2,
            'arrows': 'to;from'
        }
    }

    # Add edges
    for edge in G.edges(data=True):
        rel_type = edge[2].get('relationship', 'Unknown')
        edge_style = edge_types.get(rel_type, {
            'color': '#000000',
            'width': 1,
            'arrows': None
        })

        edge_id = f"{edge[0]}-{edge[1]}"
        edge_data[edge_id] = {
            'from': edge[0],
            'to': edge[1],
            'originalColor': edge_style['color'],
            'width': edge_style['width'],
            'hidden': False
        }

        # Add title if you prefer not to rely on color/width inference
        net.add_edge(edge[0], edge[1],
                     color={'color': edge_style['color'], 'opacity': 1.0},
                     width=edge_style['width'],
                     arrows=edge_style['arrows'])

    # Data script for JavaScript
    data_script = f"""
    <script>
        var categoryInfo = {json.dumps(category_info)};
        var categoryColors = {json.dumps(category_colors)};
        var nodeData = {json.dumps(node_data)};
        var edgeData = {json.dumps(edge_data)};
    </script>
    """

    # Container div with legend inside the visualization area
    container_div = """
    <div id="visualization-container" style="display: flex; width: 100%; height: 100vh;">
        <div id="controls-panel" style="width: 250px; height: 100%; overflow-y: auto; padding: 15px; border-right: 1px solid #ccc; background: white;">
            <div class="control-section">
                <h3>DSM-5-TR Network Overview</h3>
                <div id="network-metrics" class="metrics-panel"></div>
            </div>

            <div class="control-section">
                <h3>Node Creation</h3>
                <div class="input-group">
                    <input type="text" id="node-label" placeholder="Node Label" class="full-width">
                    <select id="node-type" class="full-width">
                        <option value="disorder">Disorder</option>
                        <option value="symptom">Symptom</option>
                    </select>
                    <select id="category-select" class="full-width">
                        <!-- Populated dynamically with DSM categories -->
                    </select>
                </div>
                <button onclick="networkState.toggleNodeCreationMode()" class="button create-button">Toggle Node Creation</button>
            </div>

            <div class="control-section">
                <h3>Relationship Creation</h3>
                <select id="edge-type" class="full-width">
                    <option value="HAS_SYMPTOM">Has Symptom</option>
                    <option value="COMORBID_WITH">Comorbid With</option>
                </select>
                <button onclick="networkState.toggleEdgeCreationMode()" class="button create-button">Toggle Edge Creation</button>
            </div>

            <div class="control-section">
                <h3>Network Analysis Tools</h3>
                <div class="button-group">
                    <button onclick="networkState.removeHighestDegreeNode()" class="button attack-button">Remove Most Connected Node</button>
                    <button onclick="networkState.removeRandomNode()" class="button attack-button">Remove Random Node</button>
                    <button onclick="networkState.removeSelectedNodes()" class="button attack-button">Remove Selected Nodes</button>
                    <button onclick="networkState.removeSelectedEdges()" class="button attack-button">Remove Selected Edges</button>
                    <button onclick="networkState.removeRandomEdges(0.1)" class="button attack-button">Remove 10% Random Edges</button>
                    <button onclick="networkState.removeHighestBetweennessEdges(0.1)" class="button attack-button">Remove 10% Central Edges</button>
                    <button onclick="networkState.restoreNetwork()" class="button restore-button">Restore Network</button>
                </div>
            </div>

            <div class="control-section">
                <h3>Search & Navigation</h3>
                <div class="input-group">
                    <input type="text" id="disorder-search" placeholder="Search disorders..." class="search-input full-width">
                    <button onclick="networkState.searchDisorder()" class="button search-button">Search</button>
                    <button onclick="networkState.toggleFreeze()" class="button freeze-button">Freeze Layout</button>
                </div>
                <div class="input-group">
                    <input type="text" id="disorder-isolation" placeholder="Enter up to 3 disorders, separated by commas..." class="search-input full-width">
                    <button onclick="networkState.isolateMultipleDisorders()" class="button search-button">Isolate Disorders</button>
                </div>
            </div>
        </div>

        <div id="network-container" style="flex-grow: 1; height: 100%; position: relative;">
            <div id="creation-mode-indicator" class="mode-indicator"></div>
            <div id="mynetwork"></div>

            <!-- Floating Legend Box -->
            <div id="network-legend" style="
                position:absolute; 
                top:20px; 
                left:20px; 
                background:rgba(255,255,255,0.95); 
                padding:10px; 
                border-radius:4px; 
                box-shadow:0 2px 8px rgba(0,0,0,0.1); 
                font-size:12px; 
                z-index:2000;
                max-width: 200px;
            ">
                <strong>Legend</strong>
                <div style="margin-top:10px;">
                    <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:grey;vertical-align:middle;margin-right:5px;"></span>
                    <strong>Disorder</strong>
                    <div style="font-size:11px;color:#555;">(Dot-shaped, category-colored)</div>
                </div>

                <div style="margin-top:10px;">
                    <span style="display:inline-block;width:0;height:0;vertical-align:middle;margin-right:5px;
                                 border-left:6px solid transparent;
                                 border-right:6px solid transparent;
                                 border-bottom:10px solid grey;"></span>
                    <strong>Symptom</strong>
                    <div style="font-size:11px;color:#555;">(Triangle-shaped)</div>
                </div>

                <div style="margin-top:15px;">
                    <span style="color:#0000FF; margin-right:5px;">→</span><strong>Has Symptom</strong>
                    <div style="font-size:11px;color:#555;">(Blue, disorder → symptom)</div>
                </div>

                <div style="margin-top:10px;">
                    <span style="color:#FF0000; margin-right:5px;">↔</span><strong>Comorbid With</strong>
                    <div style="font-size:11px;color:#555;">(Red, bidirectional between disorders)</div>
                </div>
            </div>
        </div>

        <div id="legend" class="legend-panel">
            <h3>DSM-5-TR Categories</h3>
            <div class="legend-container"></div>
        </div>
    </div>
    """

    style = """
    <style>
        body { 
            margin: 0; 
            padding: 0; 
            overflow: hidden; 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
        }

        /* Main Container */
        #visualization-container { 
            display: flex; 
            width: 100%; 
            height: 100vh;
            background: #ffffff;
        }

        /* Control Panel */
        .control-section {
            margin-bottom: 20px;
            padding: 15px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }

        .control-section h3 {
            margin: 0 0 15px 0;
            font-size: 14px;
            color: #333;
            font-weight: 600;
            border-bottom: 2px solid #f0f0f0;
            padding-bottom: 8px;
        }

        /* Form Controls */
        .full-width {
            width: 100%;
            margin-bottom: 8px;
        }

        .input-group input, 
        .input-group select {
            width: 100%;
            padding: 8px;
            margin-bottom: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 13px;
        }

        .button {
            width: 100%;
            padding: 8px 12px;
            margin: 4px 0;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.2s ease;
        }

        /* Button Types */
        .create-button { 
            background-color: #4444ff; 
            color: white; 
        }
        .create-button:hover { 
            background-color: #3333cc;
            transform: translateY(-1px);
        }

        .attack-button { 
            background-color: #ff4444; 
            color: white; 
        }
        .attack-button:hover { 
            background-color: #cc3333;
            transform: translateY(-1px);
        }

        .restore-button { 
            background-color: #44aa44; 
            color: white; 
        }
        .restore-button:hover { 
            background-color: #338833;
            transform: translateY(-1px);
        }

        /* Legend Panel */
        .legend-panel {
            width: 280px;
            height: 100%;
            overflow-y: auto;
            padding: 20px;
            border-left: 1px solid #e0e0e0;
            background: white;
        }

        .legend-item {
            padding: 12px;
            margin-bottom: 8px;
            border-radius: 6px;
            transition: all 0.2s ease;
            cursor: pointer;
        }

        .legend-item:hover {
            transform: translateX(2px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .legend-item.active {
            box-shadow: 0 0 0 2px #4444ff;
        }

        /* Metrics Panel */
        .metrics-panel {
            font-family: monospace;
            font-size: 12px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
            line-height: 1.4;
        }

        /* Mode Indicator */
        .mode-indicator {
            position: absolute;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            padding: 8px 16px;
            background-color: rgba(255, 255, 255, 0.95);
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            z-index: 1000;
            font-size: 13px;
            display: none;
        }

        /* Context Menu */
        #context-menu {
            position: absolute;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 8px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            z-index: 1000;
        }

        #context-menu button {
            display: block;
            width: 100%;
            padding: 8px 16px;
            border: none;
            background: none;
            text-align: left;
            cursor: pointer;
            font-size: 13px;
        }

        #context-menu button:hover {
            background-color: #f0f0f0;
        }
    </style>
    """

    network_manipulation_script = """
    <script>
    class NetworkState {
        constructor() {
            this.originalNodes = new Map();
            this.originalEdges = new Map();
            this.removedNodes = new Map();
            this.removedEdges = new Map();
            this.creationMode = 'none';
            this.edgeCreationState = { fromNode: null };
            this.isLayoutFrozen = false;

            this.elements = {
                networkMetrics: document.querySelector('#network-metrics'),
                creationModeIndicator: document.querySelector('#creation-mode-indicator'),
                nodeType: document.querySelector('#node-type'),
                edgeType: document.querySelector('#edge-type'),
                categorySelect: document.querySelector('#category-select'),
                disorderSearch: document.querySelector('#disorder-search'),
                freezeButton: document.querySelector('.freeze-button')
            };
        }

        init() {
            this.bindEvents();
            this.initializeNetwork();
            this.populateCategorySelect();
        }

        populateCategorySelect() {
            const categories = Object.keys(categoryInfo).sort();
            const select = this.elements.categorySelect;
            categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category;
                option.textContent = category;
                select.appendChild(option);
            });
        }

        updateMetrics() {
            const visibleNodes = nodes.get().filter(node => !node.hidden);
            const visibleEdges = edges.get().filter(edge => !edge.hidden);

            // Only show visible node and edge counts
            let metricsHTML = `
                <div>Visible Nodes: ${visibleNodes.length}/${this.originalNodes.size}</div>
                <div>Visible Edges: ${visibleEdges.length}/${this.originalEdges.size}</div>
            `;

            this.elements.networkMetrics.innerHTML = metricsHTML;
        }

        createNode(nodeLabel, position = null) {
            if (!nodeLabel) return;

            const nodeType = this.elements.nodeType.value;
            const selectedCategory = this.elements.categorySelect.value;
            const isDisorder = nodeType === 'disorder';

            const nodeDataObj = {
                id: `node_${Date.now()}`,
                label: nodeLabel,
                color: {
                    background: categoryColors[selectedCategory],
                    border: isDisorder ? '#2B7CE9' : '#008000'
                },
                size: isDisorder ? 80 : 75,
                shape: isDisorder ? 'dot' : 'triangle',
                category: selectedCategory,
                hidden: false,
                title: `Category: ${selectedCategory}`
            };

            if (position) {
                nodeDataObj.x = position.x;
                nodeDataObj.y = position.y;
            }

            nodes.add(nodeDataObj);
            this.updateMetrics();
        }

        toggleNodeCreationMode() {
            this.creationMode = this.creationMode === 'node' ? 'none' : 'node';
            this.edgeCreationState.fromNode = null;
            this.updateCreationModeIndicator();
        }

        toggleEdgeCreationMode() {
            this.creationMode = this.creationMode === 'edge' ? 'none' : 'edge';
            this.edgeCreationState.fromNode = null;
            this.updateCreationModeIndicator();
        }

        handleNetworkClick(params) {
            if (this.creationMode === 'node' && params.nodes.length === 0) {
                const nodeLabel = prompt('Enter node label:');
                if (nodeLabel) {
                    this.createNode(nodeLabel, params.pointer.canvas);
                }
            }

            if (this.creationMode === 'edge' && params.nodes.length === 1) {
                if (!this.edgeCreationState.fromNode) {
                    this.edgeCreationState.fromNode = params.nodes[0];
                    this.showStatus('Select target node');
                } else {
                    const fromNode = this.edgeCreationState.fromNode;
                    const toNode = params.nodes[0];

                    if (fromNode === toNode) {
                        this.showStatus('Self-loops not allowed');
                        this.edgeCreationState.fromNode = null;
                        return;
                    }

                    const edgeType = this.elements.edgeType.value;
                    const edgeColor = edgeType === 'HAS_SYMPTOM' ? '#0000FF' : '#FF0000';

                    edges.add({
                        from: fromNode,
                        to: toNode,
                        color: { color: edgeColor, opacity: 1.0 },
                        width: edgeType === 'HAS_SYMPTOM' ? 1 : 2,
                        arrows: edgeType === 'HAS_SYMPTOM' ? 'to' : 'to;from',
                        title: edgeType,
                        hidden: false
                    });

                    this.edgeCreationState.fromNode = null;
                    this.updateMetrics();
                    this.showStatus('Edge created');
                }
            }
        }

        bindEvents() {
            network.on('stabilizationIterationsDone', () => {
                nodes.forEach(node => this.originalNodes.set(node.id, {...node}));
                edges.forEach(edge => this.originalEdges.set(edge.id, {...edge}));
                this.updateMetrics();
            });

            network.on('click', (params) => this.handleNetworkClick(params));

            network.on('oncontext', (params) => {
                params.event.preventDefault();
                const position = params.pointer.DOM;

                const existingMenu = document.getElementById('context-menu');
                if (existingMenu) existingMenu.remove();

                const selectedNodes = network.getSelectedNodes();
                const selectedEdges = network.getSelectedEdges();

                if (selectedNodes.length > 0 || selectedEdges.length > 0) {
                    this.showContextMenu(position.x, position.y, selectedNodes, selectedEdges);
                }
            });

            document.addEventListener('click', (event) => {
                const contextMenu = document.getElementById('context-menu');
                if (contextMenu && !contextMenu.contains(event.target)) {
                    contextMenu.remove();
                }
            });

            document.addEventListener('keydown', (event) => {
                if (event.key === 'Escape') {
                    this.creationMode = 'none';
                    this.edgeCreationState.fromNode = null;
                    this.updateCreationModeIndicator();
                }
            });
        }

        showContextMenu(x, y, selectedNodes, selectedEdges) {
            const menu = document.createElement('div');
            menu.id = 'context-menu';
            menu.style.left = `${x}px`;
            menu.style.top = `${y}px`;

            if (selectedNodes.length > 0) {
                const removeNodeButton = document.createElement('button');
                removeNodeButton.textContent = `Remove Selected Node${selectedNodes.length > 1 ? 's' : ''} (${selectedNodes.length})`;
                removeNodeButton.onclick = () => {
                    this.removeSelectedNodes();
                    menu.remove();
                };
                menu.appendChild(removeNodeButton);
            }

            if (selectedEdges.length > 0) {
                const removeEdgeButton = document.createElement('button');
                removeEdgeButton.textContent = `Remove Selected Edge${selectedEdges.length > 1 ? 's' : ''} (${selectedEdges.length})`;
                removeEdgeButton.onclick = () => {
                    this.removeSelectedEdges();
                    menu.remove();
                };
                menu.appendChild(removeEdgeButton);
            }

            document.body.appendChild(menu);
        }

        removeHighestDegreeNode() {
            let maxDegree = -1;
            let maxDegreeNode = null;

            nodes.forEach(node => {
                if (node.hidden) return;
                const connectedEdges = network.getConnectedEdges(node.id);
                const visibleEdges = connectedEdges.filter(edgeId => !edges.get(edgeId).hidden);
                if (visibleEdges.length > maxDegree) {
                    maxDegree = visibleEdges.length;
                    maxDegreeNode = node;
                }
            });

            if (maxDegreeNode) {
                this.removedNodes.set(maxDegreeNode.id, maxDegreeNode);
                nodes.update({id: maxDegreeNode.id, hidden: true});
                this.updateMetrics();
            }
        }

        removeRandomNode() {
            const visibleNodes = nodes.get().filter(node => !node.hidden);
            if (visibleNodes.length > 0) {
                const randomIndex = Math.floor(Math.random() * visibleNodes.length);
                const node = visibleNodes[randomIndex];
                this.removedNodes.set(node.id, node);
                nodes.update({id: node.id, hidden: true});
                this.updateMetrics();
            }
        }

        removeSelectedNodes() {
            const selectedNodes = network.getSelectedNodes();
            selectedNodes.forEach(nodeId => {
                const node = nodes.get(nodeId);
                if (!node.hidden) {
                    this.removedNodes.set(nodeId, node);
                    nodes.update({id: nodeId, hidden: true});
                }
            });
            this.updateMetrics();
        }

        removeSelectedEdges() {
            const selectedEdges = network.getSelectedEdges();
            selectedEdges.forEach(edgeId => {
                const edge = edges.get(edgeId);
                if (!edge.hidden) {
                    this.removedEdges.set(edgeId, edge);
                    edges.update({id: edgeId, hidden: true});
                }
            });
            this.updateMetrics();
        }

        removeRandomEdges(percentage) {
            const visibleEdges = edges.get().filter(edge => !edge.hidden);
            const numToRemove = Math.floor(visibleEdges.length * percentage);

            for (let i = 0; i < numToRemove; i++) {
                const randomIndex = Math.floor(Math.random() * visibleEdges.length);
                const edge = visibleEdges.splice(randomIndex, 1)[0];
                this.removedEdges.set(edge.id, edge);
                edges.update({id: edge.id, hidden: true});
            }

            this.updateMetrics();
        }

        removeHighestBetweennessEdges(percentage) {
            // Approximate central edges by node degrees sum
            const visibleEdges = edges.get().filter(edge => !edge.hidden);
            const edgeScores = visibleEdges.map(edge => {
                const fromDegree = network.getConnectedEdges(edge.from).length;
                const toDegree = network.getConnectedEdges(edge.to).length;
                return {id: edge.id, score: fromDegree + toDegree};
            });

            edgeScores.sort((a,b) => b.score - a.score);
            const numToRemove = Math.floor(edgeScores.length * percentage);
            const edgesToRemove = edgeScores.slice(0, numToRemove).map(e => e.id);

            edgesToRemove.forEach(edgeId => {
                const edge = edges.get(edgeId);
                if (!edge.hidden) {
                    this.removedEdges.set(edgeId, edge);
                    edges.update({id: edgeId, hidden: true});
                }
            });

            this.updateMetrics();
        }

        restoreNetwork() {
            this.removedNodes.forEach(node => {
                nodes.update({id: node.id, hidden: false});
            });

            this.removedEdges.forEach(edge => {
                edges.update({id: edge.id, hidden: false});
            });

            this.removedNodes.clear();
            this.removedEdges.clear();
            this.updateMetrics();
        }

        toggleFreeze() {
            this.isLayoutFrozen = !this.isLayoutFrozen;
            network.setOptions({
                physics: {
                    enabled: !this.isLayoutFrozen
                }
            });

            const freezeButton = this.elements.freezeButton;
            freezeButton.textContent = this.isLayoutFrozen ? 'Unfreeze Layout' : 'Freeze Layout';
            freezeButton.classList.toggle('frozen', this.isLayoutFrozen);
        }

        searchDisorder() {
            const searchTerm = this.elements.disorderSearch.value.toLowerCase();
            const foundNodes = nodes.get({
                filter: node => 
                    !node.hidden &&
                    node.shape === 'dot' &&
                    node.label.toLowerCase().includes(searchTerm)
            });

            if (foundNodes.length > 0) {
                network.focus(foundNodes[0].id, {
                    scale: 1.5,
                    animation: {
                        duration: 1000,
                        easingFunction: 'easeInOutQuad'
                    }
                });
                network.selectNodes([foundNodes[0].id]);
            } else {
                this.showStatus('Disorder not found');
            }
        }

        // Uses color/width inference to identify edges
        isolateMultipleDisorders() {
            const input = document.querySelector('#disorder-isolation').value.trim().toLowerCase();
            if (!input) {
                this.showStatus('No disorders entered');
                return;
            }

            const disorderNames = input.split(',').map(name => name.trim()).filter(name => name.length > 0).slice(0, 3);
            if (disorderNames.length === 0) {
                this.showStatus('No valid disorders entered');
                return;
            }

            // Hide all nodes and edges first
            nodes.update(nodes.get().map(node => ({ id: node.id, hidden: true })));
            edges.update(edges.get().map(edge => ({ id: edge.id, hidden: true })));

            const allNodes = nodes.get();
            const chosenDisorders = [];

            for (const name of disorderNames) {
                const found = allNodes.filter(node =>
                    node.shape === 'dot' &&
                    node.label.toLowerCase().includes(name)
                );
                if (found.length > 0) {
                    chosenDisorders.push(found[0]);
                } else {
                    this.showStatus(`No matches found for: ${name}`);
                }
            }

            if (chosenDisorders.length === 0) {
                this.showStatus('No disorders isolated');
                return;
            }

            const chosenDisorderIds = new Set(chosenDisorders.map(d => d.id));
            const visibleNodeIds = new Set(chosenDisorderIds);

            // Show chosen disorders
            chosenDisorders.forEach(disorder => {
                nodes.update({ id: disorder.id, hidden: false });
            });

            // Infer relationships by originalColor/width
            // HAS_SYMPTOM: #0000FF / width=1
            // COMORBID_WITH: #FF0000 / width=2
            edges.get().forEach(edge => {
                const edgeKey = edge.from + "-" + edge.to;
                const edgeInfo = edgeData[edgeKey];
                if (!edgeInfo) return;

                const fromNode = nodes.get(edge.from);
                const toNode = nodes.get(edge.to);

                const isBlueHasSymptom = edgeInfo.originalColor === '#0000FF' && edgeInfo.width === 1;
                const isRedComorbid = edgeInfo.originalColor === '#FF0000' && edgeInfo.width === 2;

                if (isBlueHasSymptom) {
                    // HAS_SYMPTOM
                    if (chosenDisorderIds.has(edge.from) && toNode.shape === 'triangle') {
                        edges.update({ id: edge.id, hidden: false });
                        nodes.update({ id: edge.to, hidden: false });
                        visibleNodeIds.add(edge.to);
                    } else if (chosenDisorderIds.has(edge.to) && fromNode.shape === 'triangle') {
                        // If reversed direction
                        edges.update({ id: edge.id, hidden: false });
                        nodes.update({ id: edge.from, hidden: false });
                        visibleNodeIds.add(edge.from);
                    }
                } else if (isRedComorbid) {
                    // COMORBID_WITH: show if both ends are chosen disorders
                    if (chosenDisorderIds.has(edge.from) && chosenDisorderIds.has(edge.to)) {
                        edges.update({ id: edge.id, hidden: false });
                    }
                }
            });

            if (visibleNodeIds.size > 0) {
                network.fit({
                    nodes: Array.from(visibleNodeIds),
                    animation: {
                        duration: 1000,
                        easingFunction: 'easeInOutQuad'
                    }
                });
                this.updateMetrics();
                this.showStatus('Disorders isolated with their symptoms and internal comorbidities');
            } else {
                this.showStatus('No disorders or symptoms found');
            }
        }

        updateCreationModeIndicator() {
            const indicator = this.elements.creationModeIndicator;
            indicator.textContent = `Creation Mode: ${this.creationMode.charAt(0).toUpperCase() + this.creationMode.slice(1)}`;
            indicator.style.display = this.creationMode !== 'none' ? 'block' : 'none';
        }

        showStatus(message) {
            const indicator = this.elements.creationModeIndicator;
            indicator.textContent = message;
            indicator.style.display = 'block';
            setTimeout(() => {
                indicator.style.display = 'none';
            }, 2000);
        }

        initializeNetwork() {
            network.setOptions({
                nodes: {
                    font: {
                        size: 70, 
                        face: 'arial'
                    },
                    scaling: {
                        min: 60,
                        max: 70
                    }
                },
                 edges: {
            smooth: {
                enabled: true,
                type: 'continuous'
                    }
                },
                physics: {
                    enabled: true,
                    forceAtlas2Based: {
                        gravitationalConstant: -500,
                        centralGravity: 0.005,
                        springLength: 400,
                        springConstant: 0.08
                },
                    solver: 'forceAtlas2Based',
                    stabilization: {
                        enabled: true,
                        iterations: 2000,
                        updateInterval: 25
                    }
                },
                interaction: {
                    hover: true,
                    multiselect: true,
                    navigationButtons: true
                }
            });
        }
    }

    class LegendManager {
        constructor() {
            this.legendContainer = document.querySelector('#legend .legend-container');
            this.activeItem = null;
            this.visibilityMap = new Map();
        }

        init() {
            this.createLegend();
        }

        createLegend() {
            // "Show All" button
            const resetButton = document.createElement('button');
            resetButton.textContent = 'Show All Categories';
            resetButton.className = 'button restore-button';
            resetButton.style.marginBottom = '15px';
            resetButton.onclick = () => this.resetVisualization();
            this.legendContainer.appendChild(resetButton);

            // Category items
            Object.entries(categoryInfo)
                .sort(([a], [b]) => a.localeCompare(b))
                .forEach(([category, info]) => {
                    const item = this.createLegendItem(category, info);
                    this.legendContainer.appendChild(item);
                });
        }

        createLegendItem(category, info) {
            const item = document.createElement('div');
            item.className = 'legend-item';
            item.style.borderLeft = `4px solid ${categoryColors[category]}`;

            const content = `
                <strong>${category}</strong>
                <div style="font-size: 0.9em; color: #666;">
                    Disorders: ${info.disorders.length}
                    <br>
                    Symptoms: ${info.symptoms.length}
                </div>
            `;

            item.innerHTML = content;
            item.onclick = () => this.handleLegendClick(item, category);
            return item;
        }

        handleLegendClick(item, category) {
            console.log('Legend clicked:', category);

            // Toggle behavior
            if (this.activeItem === item) {
                this.resetVisualization();
                return;
            }

            if (this.activeItem) {
                this.activeItem.classList.remove('active');
            }

            item.classList.add('active');
            this.activeItem = item;
            this.updateVisibility(category);
        }

        updateVisibility(category) {
            console.log('Updating visibility for:', category);
            this.visibilityMap.clear();

            // Hide all nodes first
            nodes.update(nodes.get().map(node => ({
                id: node.id,
                hidden: true
            })));

            // Get all disorders in this category
            const categoryDisorders = nodes.get().filter(node => 
                node.category === category && 
                node.shape === 'dot'
            );
            console.log(`Found ${categoryDisorders.length} disorders in category`);

            // For each disorder, show it and connected nodes
            categoryDisorders.forEach(disorder => {
                nodes.update({ id: disorder.id, hidden: false });
                this.visibilityMap.set(disorder.id, true);

                const connectedEdges = network.getConnectedEdges(disorder.id);
                connectedEdges.forEach(edgeId => {
                    const edge = edges.get(edgeId);
                    edges.update({ id: edgeId, hidden: false });

                    const otherNodeId = edge.from === disorder.id ? edge.to : edge.from;
                    nodes.update({ id: otherNodeId, hidden: false });
                    this.visibilityMap.set(otherNodeId, true);
                });
            });

            // Update edge visibility based on visible nodes
            edges.update(edges.get().map(edge => ({
                id: edge.id,
                hidden: !(this.visibilityMap.has(edge.from) && this.visibilityMap.has(edge.to))
            })));

            // Fit the view to visible nodes
            const visibleNodes = Array.from(this.visibilityMap.keys());
            if (visibleNodes.length > 0) {
                network.fit({
                    nodes: visibleNodes,
                    animation: {
                        duration: 1000,
                        easingFunction: 'easeInOutQuad'
                    }
                });
            }
        }

        resetVisualization() {
            console.log('Resetting visualization');

            if (this.activeItem) {
                this.activeItem.classList.remove('active');
                this.activeItem = null;
            }

            // Show all nodes and edges
            nodes.update(nodes.get().map(node => ({
                id: node.id,
                hidden: false
            })));

            edges.update(edges.get().map(edge => ({
                id: edge.id,
                hidden: false
            })));

            network.fit({
                animation: {
                    duration: 1000,
                    easingFunction: 'easeInOutQuad'
                }
            });
        }
    }

    const networkState = new NetworkState();
    const legendManager = new LegendManager();

    window.addEventListener('load', () => {
        networkState.init();
        legendManager.init();
    });
    </script>
    """

    legend_script = """
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            console.log('Network visualization loaded successfully');
        });
    </script>
    """

    # Generate the base HTML from pyvis
    html = net.generate_html(notebook=False)
    # Insert style and scripts into the HTML
    html = html.replace('</head>', f'{style}{data_script}</head>')
    html = html.replace('<body>', f'<body>{container_div}')
    html = html.replace('</body>', f'{network_manipulation_script}{legend_script}</body>')

    # Write the complete HTML file
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html)

    # Print network analysis if requested
    if print_analysis:
        metrics = calculate_network_metrics(G)
        print("\nNetwork Analysis:")
        print(f"Nodes: {metrics['node_count']}")
        print(f"Edges: {metrics['edge_count']}")
        print(f"Average Degree: {metrics['avg_degree']:.2f}")
        print(f"Density: {metrics['density']:.2f}")
        print(f"Clustering Coefficient: {metrics['clustering_coefficient']:.2f}")
        print(f"Connected Components: {metrics['connected_components']}")
        print(f"Largest Component Size: {metrics['largest_component_size']}")
        if metrics['avg_shortest_path'] != float('inf'):
            print(f"Average Shortest Path: {metrics['avg_shortest_path']:.2f}")
        else:
            print("Average Shortest Path: N/A (Graph is disconnected)")

        print("\nCategory Analysis:")
        for category, stats in metrics['category_metrics'].items():
            print(f"\n{category}:")
            print(f"  Disorders: {stats['disorders']}")
            print(f"  Symptoms: {stats['symptoms']}")
            print(f"  Internal Edges: {stats['internal_edges']}")


def main():
    """Main function for loading data and creating the visualization."""
    try:
        print("Starting data loading process...")

        # Check if file exists
        if not os.path.exists('merged_disorders_data.csv'):
            print("Error: merged_disorders_data.csv not found in current directory")
            print("Current working directory:", os.getcwd())
            return

        # Load the merged data with error handling
        try:
            categories_df = pd.read_csv('merged_disorders_data.csv')
            print(f"Successfully loaded data with {len(categories_df)} rows")
            print("Columns found:", categories_df.columns.tolist())
        except Exception as e:
            print(f"Error loading CSV file: {str(e)}")
            return

        # Convert categories to strings
        categories_df['source_category'] = categories_df['source_category'].astype(str)
        categories_df['target_category'] = categories_df['target_category'].astype(str)

        print("\nCreating network...")
        G = create_complete_graph(None, None, categories_df)
        print(f"Network created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")

        # Initialize category counting
        category_counts = defaultdict(lambda: {'disorders': 0, 'symptoms': 0})

        # Count nodes by category
        for node, attr in G.nodes(data=True):
            category = str(attr.get('category', 'Uncategorized'))
            node_type = 'disorders' if attr.get('bipartite') == 0 else 'symptoms'
            category_counts[category][node_type] += 1

        print("\nNetwork Statistics:")
        print(f"Total nodes: {G.number_of_nodes()}")
        print(f"Total edges: {G.number_of_edges()}")

        print("\nCategory Statistics:")
        category_keys = [str(key) for key in category_counts.keys()]
        for category in sorted(category_keys):
            counts = category_counts[category]
            print(f"{category}:")
            print(f"  Disorders: {counts['disorders']}")
            print(f"  Symptoms: {counts['symptoms']}")

        print("\nCreating visualization...")
        visualization_path = os.path.abspath('network_with_categories.html')
        visualize_graph(G, html_file=visualization_path)
        print(f"\nVisualization file created at: {visualization_path}")

        # Open the visualization once
        try:
            webbrowser.open('file://' + visualization_path)
            print("Visualization should open in your default web browser")
        except Exception as e:
            print(f"Error opening visualization in browser: {str(e)}")
            print("Please try opening the file manually at:", visualization_path)

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()