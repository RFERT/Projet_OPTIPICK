from streamlit.runtime.scriptrunner import get_script_run_ctx
# Pour éviter la réitération compulsive de root.mainloop une fois que streamlit est lancé
import tkinter as tk

from src.loader import load_all_data
from src.Run_days import run_day1, run_day2, run_day3, run_day4, run_day5
from app_streamlit import run_app


def launch_streamlit(root):
    """Ferme Tkinter et lance l'app Streamlit."""
    root.destroy()
    run_app()

def launch_console(root):
    """Ferme Tkinter et lance le mode console."""
    root.destroy()
    run_console()


def run_console():
    """Mode console : lance les 5 jours d'analyse dans le terminal."""
    warehouse, products, agents, orders = load_all_data()
    print("Donnees chargees depuis JSON et converties en objets Python")

    print("\n=== RESULTATS ===")
    
    # jours 1 et 2 : allocation des commandes
    run_day1(warehouse, products, agents, orders)
    result_day2 = run_day2(warehouse, products, agents, orders)
    
    # jours 3 a 5 : optimisation
    run_day3(result_day2.assignments, agents, orders, products, warehouse)
    run_day4(result_day2.assignments, agents, orders, products)
    run_day5(orders, products, agents, warehouse)


def main():
    """Affiche une fenetre Tkinter pour choisir entre console et Streamlit."""
    root = tk.Tk()
    root.title("Choix de l'interface")
    root.geometry("300x150")
    tk.Label(root, text="Choisissez l'interface:").pack(pady=10)
    tk.Button(root, text="Streamlit", command=lambda: launch_streamlit(root)).pack(pady=5)
    tk.Button(root, text="Console", command=lambda: launch_console(root), default="disabled").pack(pady=5)
    # En vrai le bouton est inutile puisque le mode console est la valeur par defaut si on ne lance pas via 'streamlit run main.py', mais c'est pour faire joli et montrer qu'on a pensé à tout, et qu'on as pas eu le temps d'ajouter des manipulation de commandes de terminal et d'OS pour réouvrir en "streamlit run main.py", et que ça fait plus pro que de juste lancer le mode console par défaut sans rien demander à l'utilisateur, même si c'est un peu redondant et inutile dans les faits (commentaire non PEP8-frienldy désolé)
    root.mainloop()


if __name__ == "__main__":
    try:
        # renvoie le contexte d'execution de streamlit 
        # (pour éviter de se faire bloquer par root.mainloop,
        # qui est incompatible avec Streamlit 
        # (les 2 se relancent en boucle donc le programme n'avance 
        # jamais au delà de la première itération de streamlit))
        # GROSSE GALERE à trouver !!!!!!!
        if get_script_run_ctx() is not None:
            run_app()
        else:
            main()
    except ImportError:
        main()
