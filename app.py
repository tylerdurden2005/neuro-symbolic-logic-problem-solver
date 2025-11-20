from tkinter import *
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import tkinter as tk

from module1.client import TextFormalizer
from module2.logical_exp_parser import LogicalExpressionParser
from module2.logical_exp_parser import TreeToStringConverter
from module2.prenex_normal_from import Prenexer
from module2.scolem_normal_form import Skolemizer
from module2.resolution import resolution
from module3.explanation import Proofer

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("~Neuro-Symbolic~")
        self.geometry("1200x1050")
        self.configure(bg="#1e1e1e")
        self.style = ttk.Style()
        self.create_widgets()

    def create_widgets(self):
        self.style.configure(
            'Custom.Label',
            background='#2d2d30',
            foreground='#ffffff',
            relief='solid',
            font=("Segoe UI", 10),
        )

        self.style.configure(
            'Title.Label',
            background='#2d2d30',
            foreground='#569cd6',
            font=("Segoe UI", 14, "bold"),
        )

        self.frame1 = ttk.Frame(self, width=1100, height=400, style="Custom.Label")
        self.frame1.pack(padx=10, pady=10)

        self.label1 = ttk.Label(self.frame1,
                                text="Введите утверждения:",
                                style="Title.Label",
                                width=100)
        self.label1.place(relx=0.02, rely=0.0005, anchor="nw")

        self.ScrolledText = ScrolledText(self.frame1,
                                         width=40,
                                         font=("Segoe UI", 12),
                                         bg="#252526",
                                         fg="#d4d4d4",
                                         wrap=tk.WORD,
                                         insertbackground="#569cd6",
                                         selectbackground="#264f78",
                                         borderwidth=2,
                                         relief="solid")
        self.ScrolledText.place(relx=0.02, rely=0.1, anchor="nw", relwidth=0.7, relheight=0.8)
        self.ScrolledText.vbar.config(
            width=20,
            borderwidth=2,
            cursor="hand2",
            relief="raised",
            bd=5,
            highlightthickness=2,
            highlightcolor="#3c3c3c",
            highlightbackground="#3c3c3c",
            bg="#3c3c3c",
            troughcolor="#2d2d30",
            activebackground="#454545"
        )

        self.button = tk.Button(
            self.frame1,
            text="Доказать!",
            bg="#4FC3F7",
            cursor="hand2",
            fg="white",
            font=("Segoe UI", 14, "bold"),
            relief="raised",
            bd=3,
            activebackground="#29B6F6",
            activeforeground="white",
            highlightthickness=2,
            highlightcolor="#4FC3F7",
            highlightbackground="#4FC3F7",
            command=self.process
        )
        self.button.place(
            relx=0.75,
            rely=0.2,
            anchor="nw",
            width=240,
            height=150
        )

        self.frame2 = ttk.Frame(self, width=1100, height=600, style="Custom.Label")
        self.frame2.pack(padx=20, pady=10)

        self.ScrolledText2 = ScrolledText(self.frame2,
                                          width=20,
                                          font=("Segoe UI", 12),
                                          bg="#252526",
                                          fg="#d4d4d4",
                                          wrap=tk.WORD,
                                          insertbackground="#569cd6",
                                          selectbackground="#264f78",
                                          borderwidth=2,
                                          relief="solid")
        self.ScrolledText2.place(relx=0.02, rely=0.05, anchor="nw", relwidth=0.95, relheight=0.9)
        self.ScrolledText2.configure(state='disabled')
        self.ScrolledText2.vbar.config(
            width=20,
            borderwidth=2,
            cursor="hand2",
            relief="raised",
            bd=5,
            highlightthickness=2,
            highlightcolor="#3c3c3c",
            highlightbackground="#3c3c3c",
            bg="#3c3c3c",
            troughcolor="#2d2d30",
            activebackground="#454545"
        )

    def change_all_formulas(self, text_formulas):
        logic_parser = LogicalExpressionParser()
        tree_converter = TreeToStringConverter()
        prenexer = Prenexer()
        skolemizer = Skolemizer()

        tree_formulas = []
        prenex_text = []
        skolem_text = []

        for f in text_formulas:
            formula = logic_parser.parse(f)
            prenex_formula = prenexer.build_prenex_form(formula)
            prenex_text.append(tree_converter.convert(prenex_formula))
            skolem_formula = skolemizer.build_skolem_form(prenex_formula)
            skolem_text.append(tree_converter.convert(skolem_formula))
            tree_formulas.append(skolem_formula)

        return tree_formulas, prenex_text, skolem_text

    def format_section(self, title, content_list, separator=" " * 40):
        section = [separator, title, separator]
        for i, item in enumerate(content_list, 1):
            section.append(f"{i}. {item}")
        section.append("")
        return "\n".join(section)

    def process(self):
        input_text = self.ScrolledText.get("1.0", tk.END).strip()
        if not input_text:
            self.display_result("Ошибка: Введите текст для анализа!")
            return

        # запрос к gpt
        text_formalizer = TextFormalizer()
        gpt_info = text_formalizer.formalize_text(input_text)
        text_formulas = gpt_info["formulas"]
        # преобразовать формулы
        all_formulas, prenex_text, skolem_text = self.change_all_formulas(text_formulas)
        # вызов резолюции
        resolution(all_formulas)

        result_parts = []
        result_parts.append(self.format_section("Начальные условия:", [gpt_info["raw_response"]]))
        result_parts.append(self.format_section("Предваренная нормальная форма:", prenex_text))
        result_parts.append(self.format_section("Сколемовская нормальная форма:", skolem_text))


        with open('log.txt', 'r', encoding='utf-8') as file:
            content = file.read()
            result_parts.append(self.format_section("Лог доказательства методом резолюции:", content))

        results_before_gpt = "\n".join(result_parts)
        proof = Proofer()
        result = proof.call_proofs(results_before_gpt)

        self.display_result(result)

    def display_result(self, result_text):
        self.ScrolledText2.configure(state='normal')
        self.ScrolledText2.delete("1.0", tk.END)
        self.ScrolledText2.insert("1.0", result_text)
        self.ScrolledText2.configure(state='disabled')

