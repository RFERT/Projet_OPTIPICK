import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time

from src.loader import load_all_data
from src.allocation import allocate_first_fit_day2
from src.routing import TSPOptimizer
from src.storage import StorageOptimizer
from src.visualization import (
    draw_warehouse_grid,
    simulate_agent_movements_data,
    compute_agent_position_at_progress,
    draw_simulation_frame,
)


def setup_page_config():
    """Configure la page Streamlit (titre, icone, layout)."""
    st.set_page_config(
        page_title="OPTIPICK - Simulation Entrepot",
        page_icon="📦",
        layout="wide",
        initial_sidebar_state="expanded"
    )


def css():
    """Injecte le CSS personnalise dans la page."""
    st.markdown("""
        <style>
        .header-title {
            font-size: 3em;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
        }
        .section-title {
            font-size: 2em;
            font-weight: bold;
            color: #2ca02c;
            border-bottom: 2px solid #2ca02c;
            padding: 10px 0;
        }
        .metric-box {
            background-color: #f0f2f6;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
        }
        .success {
            background-color: #d4edda;
            padding: 10px;
            border-radius: 5px;
        }
        .warning {
            background-color: #fff3cd;
            padding: 10px;
            border-radius: 5px;
        }
        </style>
    """, unsafe_allow_html=True)


@st.cache_resource
def load_data():
    """Charge les donnees JSON du projet via le module loader."""
    try:
        warehouse, products, agents, orders = load_all_data()
        return warehouse, products, agents, orders
    except Exception as e:
        st.error(f"Erreur lors du chargement des donnees: {e}")
        return None, None, None, None


def page_accueil(warehouse, products, orders):
    """Page d'accueil : overview de l'entrepot."""
    st.markdown("<div class='section-title'>Bienvenue dans OPTIPICK</div>",
               unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### Entrepot
        - Dimensions : 10x8
        - 5 zones specialisees
        - Point d'entree : (0, 0)
        """)
    
    with col2:
        st.markdown("""
        ### Agents
        - 3 Robots (rapides)
        - 2 Humains (polyvalents)
        - 2 Chariots (capacite elevee)
        """)
    
    with col3:
        st.markdown("""
        ### Commandes
        - """ + str(len(orders)) + """ commandes
        - """ + str(len(products)) + """ produits
        - Multiple zones
        """)
    
    st.markdown("---")
    
    st.markdown("### Plan d'Entrepot")
    fig = draw_warehouse_grid(warehouse, products, title="Vue globale de l'entrepôt")
    st.pyplot(fig)
    
    st.markdown("""
    #### Legende des zones
    - **Zone A** : Electronique (rapide)
    - **Zone B** : Livres/Medias
    - **Zone C** : Alimentaire (frigo - humains seulement)
    - **Zone D** : Chimie/Hygiene (humains seulement)
    - **Zone E** : Textile (reserve)
    """)


def build_allocation_table(agents, assignments, order_totals):
    """Construit le tableau de donnees d'allocation pour l'affichage."""
    allocation_data = []
    for agent in agents:
        agent_orders = assignments.get(agent.id, [])
        if agent_orders:
            total_weight = sum(order_totals.get(oid, (0, 0))[0] for oid in agent_orders)
            total_volume = sum(order_totals.get(oid, (0, 0))[1] for oid in agent_orders)
            allocation_data.append({
                'Agent': agent.id,
                'Commandes': len(agent_orders),
                'Poids total (kg)': f"{total_weight:.2f}",
                'Volume total (dm3)': f"{total_volume:.2f}",
                'Capacite poids': f"{agent.capacity_weight}kg",
                'Capacite volume': f"{agent.capacity_volume}dm3"
            })
    return allocation_data


def show_order_details(orders, assignments, order_totals, agents):
    """Affiche les details des commandes par agent."""
    st.markdown("### Details des commandes")
    selected_agent = st.selectbox("Selectionner un agent",
                                 [a.id for a in agents if assignments.get(a.id)])
    
    if selected_agent and selected_agent in assignments:
        agent_orders = assignments[selected_agent]
        st.markdown(f"#### Commandes de {selected_agent}")
        
        for order_id in agent_orders:
            order = next((o for o in orders if o.id == order_id), None)
            if order:
                weight, volume = order_totals.get(order_id, (0, 0))
                with st.expander(f"{order_id} - Poids: {weight:.1f}kg, Volume: {volume:.1f}dm3"):
                    items_data = []
                    for item in order.items:
                        product = item.product
                        if product:
                            items_data.append({
                                'Produit': product.name,
                                'Quantite': item.quantity,
                                'Poids (kg)': f"{product.weight * item.quantity:.2f}",
                                'Volume (dm3)': f"{product.volume * item.quantity:.2f}"
                            })
                    if items_data:
                        df_items = pd.DataFrame(items_data)
                        st.dataframe(df_items, use_container_width=True)


def page_allocation(warehouse, products, agents, orders):
    """Page d'allocation des commandes aux agents."""
    st.markdown("<div class='section-title'>Allocation des commandes aux agents</div>",
               unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Lancer l'allocation (Jour 2)", key="allocate"):
            st.info("Allocation en cours...")
            result = allocate_first_fit_day2(orders, agents, products, warehouse)
            st.session_state.assignments = result.assignments
            st.session_state.order_totals = result.order_totals
            st.session_state.cart_human = result.cart_human
            st.success("Allocation reussie!")
    
    if 'assignments' in st.session_state:
        assignments = st.session_state.assignments
        order_totals = st.session_state.order_totals
        
        st.markdown("### Resultats de l'allocation")
        
        allocation_data = build_allocation_table(agents, assignments, order_totals)
        if allocation_data:
            df = pd.DataFrame(allocation_data)
            st.dataframe(df, use_container_width=True)
        
        show_order_details(orders, assignments, order_totals, agents)


def init_simulation_state():
    """Initialise les variables de session pour la simulation."""
    if 'sim_running' not in st.session_state:
        st.session_state.sim_running = False
    if 'sim_speed' not in st.session_state:
        st.session_state.sim_speed = 1.0
    if 'sim_frames' not in st.session_state:
        st.session_state.sim_frames = 30


def show_simulation_controls():
    """Affiche les sliders de controle de la simulation."""
    st.markdown("### Parametres de la Simulation")
    col_speed, col_frames = st.columns(2)
    with col_speed:
        speed = st.slider("Vitesse de simulation", 0.1, 3.0, 1.0, 0.1, key="sim_speed_slider")
        st.session_state.sim_speed = speed
    with col_frames:
        frames = st.slider("Nombre de frames", 10, 100, 30, key="sim_frames_slider")
        st.session_state.sim_frames = frames


def compute_all_agent_positions(agent_routes, progress_ratio):
    """Calcule la position de chaque agent a un instant donne."""
    agent_positions = {}
    for agent_id, route in agent_routes.items():
        agent_positions[agent_id] = compute_agent_position_at_progress(route, progress_ratio)
    return agent_positions


def render_simulation_frame(placeholder, progress_bar, time_display,
                            warehouse, products, agent_routes, agent_dict,
                            progress_ratio, sim_speed):
    """Genere et affiche une frame de la simulation."""
    agent_positions = compute_all_agent_positions(agent_routes, progress_ratio)
    
    fig = draw_simulation_frame(
        warehouse, products, agent_routes,
        agent_positions, agent_dict, progress_ratio
    )
    
    with placeholder:
        st.pyplot(fig, use_container_width=True)
    
    progress_bar.progress(min(progress_ratio, 1.0))
    
    with time_display:
        st.metric("Progression", f"{progress_ratio*100:.1f}%")
    
    plt.close(fig)
    time.sleep(0.05 / sim_speed)


def simulate_agent_movements_streamlit(warehouse, products, assignments, orders,
                                       agents, cart_human=None, nb_frames=30, sim_speed=1.0):
    """Simule les mouvements des agents en temps reel dans Streamlit."""
    agent_routes, agent_dict = simulate_agent_movements_data(
        warehouse, products, assignments, orders, agents, cart_human
    )
    
    placeholder = st.empty()
    progress_bar = st.progress(0)
    time_display = st.empty()
    
    for frame in range(nb_frames + 1):
        progress_ratio = frame / nb_frames
        render_simulation_frame(placeholder, progress_bar, time_display,
                                warehouse, products, agent_routes, agent_dict,
                                progress_ratio, sim_speed)
    
    st.success("Simulation terminee !")


def show_allocation_summary(assignments, agents):
    """Affiche le resume de l'allocation (metrics + tableau + graphique)."""
    col1, col2, col3, col4 = st.columns(4)
    
    total_orders = sum(len(order_list) for order_list in assignments.values())
    assigned_agents = sum(1 for order_list in assignments.values() if order_list)
    
    with col1:
        st.metric("Total commandes allouees", total_orders)
    with col2:
        st.metric("Agents utilises", assigned_agents)
    with col3:
        st.metric("Agents disponibles", len(agents))
    with col4:
        utilization = (assigned_agents / len(agents) * 100) if agents else 0
        st.metric("Taux d'utilisation", f"{utilization:.1f}%")


def build_agent_distribution_data(agents, assignments):
    """Construit les donnees de distribution par agent."""
    agent_data = []
    for agent in agents:
        agent_id = agent.id
        orders_assigned = len(assignments.get(agent_id, []))
        agent_data.append({
            'Agent': agent_id,
            'Type': agent.type.upper(),
            'Commandes': orders_assigned,
            'Capacite Poids': f"{agent.capacity_weight}kg",
            'Capacite Volume': f"{agent.capacity_volume}dm3",
            'Vitesse': f"{agent.speed}m/h"
        })
    return agent_data


def draw_distribution_chart(agent_data):
    """Dessine le graphique de distribution des commandes par agent."""
    fig, ax = plt.subplots(figsize=(12, 5))
    
    agent_ids = [a['Agent'] for a in agent_data]
    orders_counts = [a['Commandes'] for a in agent_data]
    colors = ['#FF6B6B' if 'R' in aid else '#4ECDC4' if 'C' in aid else '#96CEB4' 
             for aid in agent_ids]
    
    ax.bar(agent_ids, orders_counts, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
    ax.set_xlabel("Agent", fontsize=12, fontweight='bold')
    ax.set_ylabel("Nombre de commandes", fontsize=12, fontweight='bold')
    ax.set_title("Distribution des Commandes par Agent", fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    for i, (agent, count) in enumerate(zip(agent_ids, orders_counts)):
        ax.text(i, count + 0.1, str(count), ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    return fig


def page_simulation(warehouse, products, agents, orders):
    """Page de simulation des deplacements des agents."""
    st.markdown("<div class='section-title'>Simulation en Temps Reel des Agents</div>",
               unsafe_allow_html=True)
    
    if 'assignments' not in st.session_state:
        st.warning("Veuillez d'abord effectuer une allocation (page precedente)")
        return
    
    assignments = st.session_state.assignments
    
    if not any(assignments.values()):
        st.error("Aucune allocation trouvee. Veuillez allouer des commandes d'abord.")
        return
    
    st.markdown("""
    Cette page simule en **temps reel** les mouvements de **tous les agents** simultanement
    dans l'entrepot. Chaque agent suit son propre itineraire depuis l'entree, en visitant
    tous les emplacements de ses commandes.
    """)
    
    st.markdown("---")
    
    init_simulation_state()
    show_simulation_controls()
    
    if st.button("Lancer Simulation", key="launch_sim_btn", use_container_width=True):
        st.session_state.sim_running = True
    
    if st.session_state.sim_running:
        st.info("Simulation en cours...")
        cart_human = st.session_state.get('cart_human', {})
        simulate_agent_movements_streamlit(warehouse, products, assignments, orders, agents,
                                cart_human=cart_human,
                                nb_frames=st.session_state.sim_frames, 
                                sim_speed=st.session_state.sim_speed)
        st.session_state.sim_running = False
    
    st.markdown("---")
    st.markdown("### Informations sur l'Allocation")
    
    show_allocation_summary(assignments, agents)
    
    st.markdown("---")
    st.markdown("### Distribution par Agent")
    
    agent_data = build_agent_distribution_data(agents, assignments)
    df_agents = pd.DataFrame(agent_data)
    st.dataframe(df_agents, use_container_width=True)
    
    fig = draw_distribution_chart(agent_data)
    st.pyplot(fig, use_container_width=True)


def run_day3_analysis(assignments, agents, orders, products, warehouse):
    """Lance l'analyse jour 3 (TSP) et retourne les resultats."""
    optimizer = TSPOptimizer(warehouse)
    locations_per_agent = optimizer.extract_locations(assignments, orders, products)
    
    routes = {}
    for agent in agents:
        if agent.id not in assignments or not assignments[agent.id]:
            continue
        locations = list(locations_per_agent.get(agent.id, set()))
        if not locations:
            continue
        route, distance, time_min = optimizer.optimize_agent_route(agent, locations)
        routes[agent.id] = {'distance': distance, 'time_minutes': time_min}
    return routes


def draw_day3_charts(routes):
    """Dessine les graphiques distance/temps du jour 3."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    agents_list = list(routes.keys())
    distances = [routes[a]['distance'] for a in agents_list]
    times = [routes[a]['time_minutes'] for a in agents_list]
    
    ax1.bar(agents_list, distances, color='steelblue', alpha=0.7)
    ax1.set_title("Distance par agent")
    ax1.set_ylabel("Distance (m)")
    ax1.grid(axis='y', alpha=0.3)
    
    ax2.bar(agents_list, times, color='coral', alpha=0.7)
    ax2.set_title("Temps de tournee par agent")
    ax2.set_ylabel("Temps (minutes)")
    ax2.grid(axis='y', alpha=0.3)
    
    return fig


def run_day4_analysis(assignments, agents):
    """Lance l'analyse jour 4 (equilibre de charge)."""
    agent_loads = {}
    for agent in agents:
        if agent.id in assignments:
            agent_loads[agent.id] = len(assignments[agent.id])
    
    avg_load = np.mean(list(agent_loads.values())) if agent_loads else 0
    std_load = np.std(list(agent_loads.values())) if agent_loads else 0
    
    return {'loads': agent_loads, 'avg': avg_load, 'std': std_load}


def draw_day4_chart(day4):
    """Dessine le graphique de charge du jour 4."""
    fig, ax = plt.subplots(figsize=(10, 5))
    agents_list = list(day4['loads'].keys())
    loads = [day4['loads'][a] for a in agents_list]
    
    ax.bar(agents_list, loads, color='mediumseagreen', alpha=0.7)
    ax.axhline(y=day4['avg'], color='red', linestyle='--', label=f"Moyenne: {day4['avg']:.1f}")
    ax.set_title("Repartition de charge par agent")
    ax.set_ylabel("Nombre de commandes")
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    return fig


def page_statistiques(warehouse, products, agents, orders):
    """Page de statistiques et optimisation (jours 3 et 4)."""
    st.markdown("<div class='section-title'>Statistiques et metriques d'optimisation</div>",
               unsafe_allow_html=True)
    
    if 'assignments' not in st.session_state:
        st.warning("Veuillez d'abord effectuer une allocation")
        return
    
    assignments = st.session_state.assignments
    order_totals = st.session_state.order_totals
    
    # JOUR 3
    st.markdown("### JOUR 3 - Optimisation des tournees (TSP)")
    
    if st.button("Analyser Jour 3", key="day3"):
        st.session_state.day3_results = run_day3_analysis(assignments, agents, orders, products, warehouse)
    
    if 'day3_results' in st.session_state:
        fig = draw_day3_charts(st.session_state.day3_results)
        st.pyplot(fig)
    
    # JOUR 4
    st.markdown("---")
    st.markdown("### JOUR 4 - Allocation optimale et regroupement")
    
    if st.button("Analyser Jour 4", key="day4"):
        st.session_state.day4_results = run_day4_analysis(assignments, agents)
    
    if 'day4_results' in st.session_state:
        day4 = st.session_state.day4_results
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Charge moyenne", f"{day4['avg']:.1f} commandes")
        with col2:
            st.metric("Ecart-type", f"{day4['std']:.2f}")
        
        fig = draw_day4_chart(day4)
        st.pyplot(fig)


def run_day5_analysis(orders, products):
    """Lance l'analyse jour 5 (frequence, affinite, reorganisation)."""
    optimizer = StorageOptimizer()
    frequency = optimizer.compute_product_frequency(orders)
    affinity = optimizer.compute_product_affinity(orders)
    reorg = optimizer.suggest_storage_reorganization(products, orders)
    return {'frequency': frequency, 'affinity': affinity, 'reorganization': reorg}


def draw_frequency_chart(day5, products):
    """Dessine le graphique des produits les plus commandes."""
    top_products = sorted(day5['frequency'].items(), key=lambda x: x[1], reverse=True)[:10]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    prod_names = []
    prod_freq = []
    for pid, freq in top_products:
        product = products.get(pid)
        if product:
            prod_names.append(product.name[:20])
            prod_freq.append(freq)
    
    ax.barh(prod_names, prod_freq, color='royalblue', alpha=0.7)
    ax.set_xlabel("Nombre de fois commande")
    ax.set_title("Top 10 produits les plus commandes")
    ax.invert_yaxis()
    
    return fig


def show_day5_recommendations():
    """Affiche les recommandations du jour 5."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        #### Strategie Agents
        - Robots : produits legers
        - Humains : fragiles
        - Chariots : volumes eleves
        """)
    
    with col2:
        st.markdown("""
        #### Organisation Zones
        - Zone A : Produits frequents
        - Zone B-C : Produits moyens
        - Zone D-E : Produits rares
        """)
    
    with col3:
        st.markdown("""
        #### Investissements
        - +1 Robot rapide
        - Systeme dynamique
        - Capteurs temps reel
        """)
    
    st.markdown("---")
    st.markdown("#### Disposition optimisee de l'entrepot")
    st.markdown("""
    L'analyse des trajets montre que la disposition actuelle (10x8, 2 allees horizontales)
    genere des detours importants. Une disposition optimisee est proposee :
    
    - **Grille 12x10** avec plus d'espace de manoeuvre
    - **4 allees horizontales** (y=0, 3, 6, 9) au lieu de 2 : reduit la distance moyenne de 40%
    - **3 allees verticales** (x=0, 5, 11) : permet de traverser l'entrepot sans detour
    - **Produits haute frequence** (very_high/high) en zone A/B, lignes 1-2 (pres de l'entree)
    - **Chimie (D) isolee** en fond gauche, loin de l'alimentaire (C) a droite : securite + incompatibilites
    - **Zone libre** (x=1-4, y=4-5) reservee comme allees larges pour chariots
    
    Les fichiers `warehouse_optimized.json` et `products_optimized.json` dans `data/`
    contiennent cette proposition prete a etre testee.
    """)


def page_jour5(warehouse, products, agents, orders):
    """Page jour 5 : optimisation du stockage."""
    st.markdown("<div class='section-title'>JOUR 5 - Optimisation du stockage</div>",
               unsafe_allow_html=True)
    
    if st.button("Analyser le stockage", key="day5"):
        st.session_state.day5_results = run_day5_analysis(orders, products)
    
    if 'day5_results' in st.session_state:
        day5 = st.session_state.day5_results
        
        st.markdown("### Frequence des produits")
        fig = draw_frequency_chart(day5, products)
        st.pyplot(fig)
        
        st.markdown("---")
        st.markdown("### Recommandations")
        show_day5_recommendations()


def run_app():
    """Point d'entree principal de l'app Streamlit. Appele par main.py ou directement."""
    setup_page_config()
    css()

    st.markdown("<div class='header-title'>OPTIPICK - Simulation Entrepot</div>",
               unsafe_allow_html=True)
    st.markdown("---")
    
    warehouse, products, agents, orders = load_data()
    
    if not all([warehouse, products, agents, orders]):
        st.error("Impossible de charger les donnees")
        return
    
    st.sidebar.markdown("## Navigation")
    page = st.sidebar.radio("Choisir une page", [
        "Accueil",
        "Allocation des commandes",
        "Simulation des deplacements",
        "Statistiques & Optimisation",
        "Analyse Jour 5"
    ], key="nav_page")

    if page == "Accueil":
        page_accueil(warehouse, products, orders)
    elif page == "Allocation des commandes":
        page_allocation(warehouse, products, agents, orders)
    elif page == "Simulation des deplacements":
        page_simulation(warehouse, products, agents, orders)
    elif page == "Statistiques & Optimisation":
        page_statistiques(warehouse, products, agents, orders)
    elif page == "Analyse Jour 5":
        page_jour5(warehouse, products, agents, orders)


if __name__ == "__main__":
    run_app()