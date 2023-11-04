import chardet
import difflib
import io
import os
import random
import requests
import unicodedata
import pyttsx3
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QKeySequence, QFont, QClipboard
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QMenu, QAction, QSystemTrayIcon

API_ENDPOINT = "http://159.223.80.140:5555/admin/vocabulary/"

def remove_accents(text):
    text = text.replace('đ', 'd').replace('Đ', 'D')
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    
class VocabularyQuiz(QWidget):
    def __init__(self, num_questions):
        super().__init__()
        self.setFixedSize(500, 250)

        self.rate_input = QLineEdit(self)
        self.rate_input.setPlaceholderText("Tốc độ đọc (0-500 từ/phút) (ưu tiên 80)")
        self.rate_input.textChanged.connect(self.set_rate)

        try:
            response = requests.get(API_ENDPOINT)
            response.raise_for_status()
            self.questions = response.json()
            random.shuffle(self.questions)
            self.questions = self.questions[:num_questions]
        except (requests.exceptions.RequestException, ValueError):
            self.questions = []
        self.current_question_index = 0
        self.num_correct_answers = 0

        self.engine = pyttsx3.init()

        self.rate = 80
        self.engine.setProperty('rate', self.rate)

        self.question_label = QLabel(self.questions[self.current_question_index]['vocabulary'], self)
        self.question_label.setAlignment(Qt.AlignCenter)
        self.question_label.setProperty('class', 'question-label')

        self.answer_input = QLineEdit(self)
        self.answer_input.setStyleSheet('''
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid gray;
                border-radius: 5px;
                padding: 2px;
            }
        ''')

        self.check_button = QPushButton('Check', self)
        self.check_button.setStyleSheet('''
            QPushButton {
                background-color: #3498DB;
                color: white;
                font-size: 16px;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
            QPushButton:pressed {
                background-color: #1F618D;
            }
        ''')
        self.check_button.clicked.connect(self.check_answer)
        self.check_button.setShortcut(QKeySequence(Qt.Key_Return))

        self.speak_button = QPushButton('Speak', self)
        self.speak_button.setObjectName('speak-button')
        self.speak_button.setStyleSheet('''
            QPushButton#speak-button {
                background-color: #2ECC71;
                color: white;
                font-size: 16px;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton#speak-button:hover {
                background-color: #27AE60;
            }
            QPushButton#speak-button:pressed {
                background-color: #1E8449;
            }
        ''')
        self.speak_button.clicked.connect(self.speak_question)

        self.speak_answer_button = QPushButton('Speak Answer', self)
        self.speak_answer_button.setObjectName('speak-answer-button')
        self.speak_answer_button.setStyleSheet('''
            QPushButton#speak-answer-button {
                background-color: #F39C12;
                color: white;
                font-size: 16px;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton#speak-answer-button:hover {
                background-color: #E67E22;
            }
            QPushButton#speak-answer-button:pressed {
                background-color: #D35400;
            }
        ''')
        self.speak_answer_button.clicked.connect(self.speak_answer)

        self.copy_button = QPushButton('Copy', self)
        self.copy_button.setObjectName('copy-button')
        self.copy_button.setStyleSheet('''
            QPushButton#copy-button {
                background-color: #9B59B6;
                color: white;
                font-size: 16px;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton#copy-button:hover {
                background-color: #8E44AD;
            }
            QPushButton#copy-button:pressed {
                background-color: #7D3C98;
            }
        ''')
        self.copy_button.clicked.connect(self.copy_question)

        self.menu_button = QPushButton('\u2630', self)
        self.menu_button.setObjectName('menu-button')
        self.menu_button.setStyleSheet('''
            QPushButton#menu-button {
                font-size: 24px;
                border: none;
                background-color: transparent;
            }
            QPushButton#menu-button:hover {
                background-color: #EAEAEA;
            }
        ''')
        self.menu_button.setFixedWidth(40)
        self.menu_button.setFixedHeight(40)
        self.menu_button.clicked.connect(self.show_menu)

        self.feedback_label = QLabel("", self)
        self.feedback_label.setAlignment(Qt.AlignCenter)
        self.feedback_label.setProperty('class', 'feedback-label')

        self.score_label = QLabel(f"Score: {self.num_correct_answers}/{num_questions}", self)
        self.score_label.setAlignment(Qt.AlignCenter)
        self.score_label.setProperty('class', 'score-label')

        self.restart_button = QPushButton('Restart', self)
        self.restart_button.setStyleSheet('''
            QPushButton {
                background-color: #E74C3C;
                color: white;
                font-size: 16px;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
            QPushButton:pressed {
                background-color: #922B21;
            }
        ''')
        self.restart_button.clicked.connect(self.restart_quiz)
        self.restart_button.setProperty('class', 'restart-button')

        button_layout1 = QHBoxLayout()
        button_layout1.addWidget(self.copy_button)
        button_layout1.addWidget(self.check_button)
        button_layout1.addWidget(self.speak_button)
        button_layout1.addWidget(self.speak_answer_button)
        button_layout1.addWidget(self.restart_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.menu_button, alignment=Qt.AlignRight)
        layout.addWidget(self.question_label)
        layout.addWidget(self.answer_input)
        layout.addWidget(self.rate_input)
        layout.addLayout(button_layout1)
        layout.addWidget(self.feedback_label)
        layout.addWidget(self.score_label)

        self.setStyleSheet('''
            QWidget {
                background-color: #FBFCFC;
                font-size: 18px;
                font-family: Arial;
            }
        ''')

        self.setWindowTitle('Vocabulary Quiz')
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(self.style().SP_FileIcon))
        self.tray_icon.show()
        self.show()

    def check_answer(self):
        user_answer = remove_accents(self.answer_input.text().strip().lower())
        correct_answer = remove_accents(self.questions[self.current_question_index]['translate'].lower())
        correct_answer_s = self.questions[self.current_question_index]['translate'].lower()

        if user_answer == correct_answer:
            self.num_correct_answers += 1
            self.feedback_label.setText("Correct!")
        elif 'synonyms' in self.questions[self.current_question_index]:
            synonyms = self.questions[self.current_question_index]['synonyms']
            match_ratio = max([difflib.SequenceMatcher(None, remove_accents(user_answer), remove_accents(synonym.lower())).ratio() for synonym in synonyms])
            if match_ratio >= 0.75:
                self.num_correct_answers += 1
                self.feedback_label.setText("Correct!")
            else:
                self.feedback_label.setText(f"Incorrect. The correct answer is '{correct_answer_s}'.")
        else:
            self.feedback_label.setText(f"Incorrect. The correct answer is '{correct_answer_s}'.")

        self.answer_input.clear()
        self.current_question_index += 1
        if self.current_question_index == len(self.questions):
            self.score_label.setText(f"Final score: {self.num_correct_answers}/{len(self.questions)}")
            self.question_label.setText("Do you want to play again?")
            self.answer_input.setPlaceholderText("Type 'yes' or 'no' and press Enter")
            self.check_button.setEnabled(False)
            self.speak_button.setEnabled(False)
            self.speak_answer_button.setEnabled(False)
            self.copy_button.setEnabled(False)
            self.restart_button.setEnabled(True)

        else:
            self.question_label.setText(self.questions[self.current_question_index]['vocabulary'])
            self.score_label.setText(f"Score: {self.num_correct_answers}/{self.current_question_index}")
            self.check_button.setDefault(True)
            self.speak_button.setEnabled(True)
            self.speak_answer_button.setEnabled(True)
            self.copy_button.setEnabled(True)

    def restart_quiz(self):
        num_questions = len(self.questions)
        self.close()
        quiz = VocabularyQuiz(num_questions)
        quiz.show()

    def set_rate(self, rate):
        try:
            self.rate = int(rate)
            self.engine.setProperty('rate', self.rate)
        except ValueError:
            pass

    def speak_question(self):
        question = self.questions[self.current_question_index]['vocabulary']
        if 'language' not in self.questions[self.current_question_index]:
            language = 'en'
        else:
            language = self.questions[self.current_question_index]['language']
        lang_code = chardet.detect(question.encode())['language']
        self.engine.setProperty('voice', f'{language}')
        self.engine.setProperty('rate', self.rate) 
        self.engine.say(question)
        self.engine.runAndWait()

    def speak_answer(self):
        answer = self.questions[self.current_question_index]['translate']
        if 'language' not in self.questions[self.current_question_index]:
            language = 'en'
        else:
            language = self.questions[self.current_question_index]['language']
        lang_code = 'vi'
        self.engine.setProperty('voice', f'{language}')
        self.engine.setProperty('rate', self.rate) 
        self.engine.say(answer)
        self.engine.runAndWait()

    def copy_question(self):
        question = self.questions[self.current_question_index]['vocabulary']
        mime_data = QMimeData()
        mime_data.setText(question)
        clipboard = QApplication.clipboard()
        clipboard.setMimeData(mime_data)

    def show_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet('''
            QMenu {
                background-color: white;
                border: 1px solid gray;
                padding: 5px;
            }
            QMenu::item {
                font-size: 18px;
                padding: 5px;
            }
            QMenu::item:selected {
                background-color: #EAEAEA;
            }
        ''')

        speak_question_action = QAction('Speak Question', self)
        speak_question_action.triggered.connect(self.speak_question)
        menu.addAction(speak_question_action)

        speak_answer_action = QAction('Speak Answer', self)
        speak_answer_action.triggered.connect(self.speak_answer)
        menu.addAction(speak_answer_action)

        copy_question_action = QAction('Copy Question', self)
        copy_question_action.triggered.connect(self.copy_question)
        menu.addAction(copy_question_action)

        menu.exec_(self.menu_button.mapToGlobal(self.menu_button.rect().bottomRight()))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            if self.check_button.isEnabled():
                self.check_button.animateClick()
            else:
                self.restart_quiz()
        else:
            super().keyPressEvent(event)

if __name__ == '__main__':
    app = QApplication([])
    num_questions_per_round = 20 
    quiz = VocabularyQuiz(num_questions_per_round)
    app.exec_()