from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.uix.progressbar import ProgressBar
import requests
import json
from threading import Thread

class WelcomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=50, spacing=30)
        
        # App title
        title = Label(
            text='MediNote', 
            font_size='48sp',
            size_hint=(1, 0.3),
            halign='center'
        )
        title.bind(size=title.setter('text_size'))
        
        # Welcome message
        welcome_msg = Label(
            text='Your Medical Document Summarizer\nUpload PDF files to get summaries and flash questions',
            font_size='18sp',
            size_hint=(1, 0.2),
            halign='center'
        )
        welcome_msg.bind(size=welcome_msg.setter('text_size'))
        
        # Start button
        start_btn = Button(
            text='Get Started',
            size_hint=(0.6, 0.2),
            pos_hint={'center_x': 0.5},
            font_size='20sp'
        )
        start_btn.bind(on_press=self.go_to_upload)
        
        layout.add_widget(title)
        layout.add_widget(welcome_msg)
        layout.add_widget(start_btn)
        
        self.add_widget(layout)
    
    def go_to_upload(self, instance):
        self.manager.current = 'upload'

class UploadScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_file = None
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # Title
        title = Label(
            text='Upload PDF File',
            font_size='24sp',
            size_hint=(1, 0.1),
            halign='center'
        )
        
        # File chooser
        self.file_chooser = FileChooserListView(
            size_hint=(1, 0.6),
            filters=['*.pdf']
        )
        self.file_chooser.bind(selection=self.on_file_select)
        
        # Selected file label
        self.file_label = Label(
            text='No file selected',
            size_hint=(1, 0.1),
            halign='center'
        )
        
        # Upload button
        self.upload_btn = Button(
            text='Upload and Process',
            size_hint=(0.6, 0.1),
            pos_hint={'center_x': 0.5},
            disabled=True
        )
        self.upload_btn.bind(on_press=self.upload_file)
        
        # Progress bar
        self.progress = ProgressBar(
            max=100,
            size_hint=(1, 0.05)
        )
        
        layout.add_widget(title)
        layout.add_widget(self.file_chooser)
        layout.add_widget(self.file_label)
        layout.add_widget(self.upload_btn)
        layout.add_widget(self.progress)
        
        self.add_widget(layout)
    
    def on_file_select(self, instance, selection):
        if selection and selection[0].endswith('.pdf'):
            self.selected_file = selection[0]
            self.file_label.text = f'Selected: {selection[0].split("/")[-1]}'
            self.upload_btn.disabled = False
        else:
            self.selected_file = None
            self.file_label.text = 'Please select a PDF file'
            self.upload_btn.disabled = True
    
    def upload_file(self, instance):
        if self.selected_file:
            self.upload_btn.disabled = True
            self.upload_btn.text = 'Processing...'
            self.progress.value = 20
            
            # Start upload in separate thread
            thread = Thread(target=self.send_file_to_server)
            thread.daemon = True
            thread.start()
    
    def send_file_to_server(self):
        try:
            # Update progress
            Clock.schedule_once(lambda dt: setattr(self.progress, 'value', 50))
            
            # Replace with your actual API endpoint
            url = "https://your-api-endpoint.com/process-pdf"
            
            with open(self.selected_file, 'rb') as file:
                files = {'pdf': file}
                response = requests.post(url, files=files, timeout=30)
            
            Clock.schedule_once(lambda dt: setattr(self.progress, 'value', 80))
            
            if response.status_code == 200:
                data = response.json()
                Clock.schedule_once(lambda dt: self.process_response(data))
            else:
                Clock.schedule_once(lambda dt: self.show_error("Server error occurred"))
                
        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_error(f"Upload failed: {str(e)}"))
    
    def process_response(self, data):
        self.progress.value = 100
        
        # Store the response data in the app
        app = App.get_running_app()
        app.summary_data = data.get('Summary', 'No summary available')
        app.flash_questions = data.get('Flash questions', [])
        
        # Navigate to results screen
        self.manager.current = 'results'
        
        # Reset upload screen
        Clock.schedule_once(self.reset_screen, 1)
    
    def reset_screen(self, dt):
        self.upload_btn.disabled = True
        self.upload_btn.text = 'Upload and Process'
        self.progress.value = 0
        self.file_label.text = 'No file selected'
    
    def show_error(self, message):
        popup = Popup(
            title='Error',
            content=Label(text=message),
            size_hint=(0.8, 0.4)
        )
        popup.open()
        
        # Reset upload button
        self.upload_btn.disabled = False
        self.upload_btn.text = 'Upload and Process'
        self.progress.value = 0

class ResultsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical')
        
        # Navigation bar
        nav_layout = BoxLayout(size_hint=(1, 0.1), spacing=10, padding=10)
        
        back_btn = Button(text='← Back', size_hint=(0.2, 1))
        back_btn.bind(on_press=self.go_back)
        
        upload_new_btn = Button(text='Upload New', size_hint=(0.2, 1))
        upload_new_btn.bind(on_press=self.upload_new)
        
        nav_layout.add_widget(back_btn)
        nav_layout.add_widget(Label())  # Spacer
        nav_layout.add_widget(upload_new_btn)
        
        # Tabbed panel
        self.tabs = TabbedPanel(do_default_tab=False, size_hint=(1, 0.9))
        
        # Summary tab
        self.summary_tab = TabbedPanelItem(text='Summary')
        summary_scroll = ScrollView()
        self.summary_label = Label(
            text='No summary available',
            text_size=(None, None),
            halign='left',
            valign='top'
        )
        summary_scroll.add_widget(self.summary_label)
        self.summary_tab.add_widget(summary_scroll)
        
        # Flash questions tab
        self.questions_tab = TabbedPanelItem(text='Flash Questions')
        questions_scroll = ScrollView()
        self.questions_layout = GridLayout(
            cols=1,
            size_hint_y=None,
            spacing=10,
            padding=20
        )
        self.questions_layout.bind(minimum_height=self.questions_layout.setter('height'))
        questions_scroll.add_widget(self.questions_layout)
        self.questions_tab.add_widget(questions_scroll)
        
        self.tabs.add_widget(self.summary_tab)
        self.tabs.add_widget(self.questions_tab)
        
        layout.add_widget(nav_layout)
        layout.add_widget(self.tabs)
        
        self.add_widget(layout)
    
    def on_enter(self):
        # Update content when screen is entered
        app = App.get_running_app()
        
        # Update summary
        summary_text = getattr(app, 'summary_data', 'No summary available')
        self.summary_label.text = summary_text
        self.summary_label.text_size = (self.summary_label.parent.width - 40, None)
        
        # Update flash questions
        self.questions_layout.clear_widgets()
        flash_questions = getattr(app, 'flash_questions', [])
        
        for i, question_data in enumerate(flash_questions):
            if isinstance(question_data, dict):
                question = question_data.get('question', f'Question {i+1}')
                answer = question_data.get('answer', 'No answer available')
            else:
                # If it's just a string
                question = str(question_data)
                answer = 'Click to reveal answer'
            
            question_btn = QuestionTile(question, answer)
            self.questions_layout.add_widget(question_btn)
    
    def go_back(self, instance):
        self.manager.current = 'welcome'
    
    def upload_new(self, instance):
        self.manager.current = 'upload'

class QuestionTile(Button):
    def __init__(self, question, answer, **kwargs):
        super().__init__(**kwargs)
        self.question = question
        self.answer = answer
        self.text = question
        self.size_hint_y = None
        self.height = '60dp'
        self.text_size = (None, None)
        self.halign = 'center'
        self.valign = 'middle'
        
        self.bind(on_press=self.show_answer)
    
    def show_answer(self, instance):
        # Create popup with answer
        answer_layout = BoxLayout(orientation='vertical', spacing=10, padding=20)
        
        question_label = Label(
            text=f'Q: {self.question}',
            text_size=(400, None),
            halign='left',
            font_size='16sp'
        )
        
        answer_label = Label(
            text=f'A: {self.answer}',
            text_size=(400, None),
            halign='left',
            font_size='14sp'
        )
        
        close_btn = Button(
            text='Close',
            size_hint=(1, 0.2)
        )
        
        answer_layout.add_widget(question_label)
        answer_layout.add_widget(answer_label)
        answer_layout.add_widget(close_btn)
        
        popup = Popup(
            title='Flash Question',
            content=answer_layout,
            size_hint=(0.9, 0.7)
        )
        
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

class MediNoteApp(App):
    def build(self):
        # Initialize data attributes
        self.summary_data = ""
        self.flash_questions = []
        
        # Create screen manager
        sm = ScreenManager()
        
        # Add screens
        sm.add_widget(WelcomeScreen(name='welcome'))
        sm.add_widget(UploadScreen(name='upload'))
        sm.add_widget(ResultsScreen(name='results'))
        
        return sm

if __name__ == '__main__':
    MediNoteApp().run()
