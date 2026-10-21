"""ERP OHADA — lanceur : ouvre chacun des logiciels dans sa propre fenêtre.  Lancer : python lanceur.py"""
import customtkinter as ctk

from shell import MODULES, assombrir, lancer_module


class Lanceur(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        self.title("ERP OHADA")
        self.geometry("860x360")
        self.resizable(False, False)
        ctk.CTkLabel(self, text="ERP OHADA", font=ctk.CTkFont(size=26, weight="bold")).pack(pady=(24, 2))
        ctk.CTkLabel(self, text="Choisissez une application", text_color="gray").pack(pady=(0, 18))
        grille = ctk.CTkFrame(self, fg_color="transparent")
        grille.pack(fill="both", expand=True, padx=20, pady=(0, 24))
        for i, (code, info) in enumerate(MODULES.items()):
            grille.grid_columnconfigure(i, weight=1, uniform="m")
            carte = ctk.CTkFrame(grille, corner_radius=12, border_width=2, border_color=info["couleur"])
            carte.grid(row=0, column=i, padx=10, sticky="nsew")
            ctk.CTkLabel(carte, text=info["titre"], font=ctk.CTkFont(size=17, weight="bold"),
                         text_color=info["couleur"]).pack(pady=(20, 6), padx=12)
            ctk.CTkLabel(carte, text=info["description"], wraplength=220, text_color="gray").pack(padx=12)
            ctk.CTkButton(carte, text="Ouvrir", fg_color=info["couleur"], hover_color=assombrir(info["couleur"]),
                          command=lambda c=code: lancer_module(c)).pack(side="bottom", pady=18)


if __name__ == "__main__":
    Lanceur().mainloop()
