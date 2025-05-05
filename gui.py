#!/usr/bin/env python
import PySimpleGUI as sg
import markdown
import webview
import re


sg.theme('Default1')
ICON = b'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'
TOGGLE_BTN_OFF = b'iVBORw0KGgoAAAANSUhEUgAAAGQAAAAoCAYAAAAIeF9DAAAPpElEQVRoge1b63MUVRY//Zo3eQHyMBEU5LVYpbxdKosQIbAqoFBraclatZ922Q9bW5b/gvpBa10+6K6WftFyxSpfaAmCEUIEFRTRAkQFFQkkJJghmcm8uqd763e6b+dOZyYJktoiskeb9OP2ne7zu+d3Hve2smvXLhqpKIpCmqaRruu1hmGsCoVCdxiGMc8wjNmapiUURalGm2tQeh3HSTuO802xWDxhmmaraZotpmkmC4UCWZZFxWKRHMcZVjMjAkQAEQqFmiORyJ+j0ei6UCgUNgyDz6uqym3Edi0KlC0227YBQN40zV2FQuHZbDa7O5fLOQBnOGCGBQTKNgzj9lgs9s9EIrE4EomQAOJaVf5IBYoHAKZpHs7lcn9rbm7+OAjGCy+8UHKsD9W3ruuRSCTyVCKR+Es8HlfC4bAPRF9fHx0/fpx+/PFH6unp4WOYJkbHtWApwhowYHVdp6qqKqqrq6Pp06fTvHnzqLq6mnWAa5qmLTYM48DevXuf7e/vf+Suu+7KVep3kIWsXbuW/7a0tDREo9Ed1dXVt8bjcbYK/MB3331HbW1t1N7eTgAIFoMfxSZTF3lU92sUMcplisJgxJbL5Sifz1N9fT01NjbSzTffXAKiaZpH+/v7169Zs+Yszr344oslFFbWQlpaWubGYrH3a2pqGmKxGCv74sWL9Pbbb1NnZyclEgmaNGmST13kUVsJ0h4wOB8EaixLkHIEKKAmAQx8BRhj+/btNHnyZNqwYQNNnDiR398wjFsTicSBDz74oPnOO+/8Gro1TbOyhWiaVh+Pxz+ura3FXwbj8OHDtHv3bgI448aNYyCg5Ouvv55mzJjBf2traykajXIf2WyWaQxWdOrUKTp//rww3V+N75GtRBaA4lkCA5NKpSiTydDq1atpyZIlfkvLstr7+/tvTyaT+MuAUhAQVVUjsVgMYABFVvzOnTvp888/Z34EIDgHjly6dCmfc3vBk4leFPd/jBwo3nHo559/pgMfHaATX59ApFZCb2NJKkVH5cARwAAUKBwDdOHChbRu3Tq/DegrnU4DlBxAwz3aQw895KpRUaCsp6urq9fDQUHxsIojR47QhAkTCNYCAO677z5acNttFI3FyCGHilaRUqk0myi2/nSaRwRMV9c1UhWFYrEozZo9mx3eyW9OMscGqexq3IJS7hlJOk+S3xTnvLyNB+L333/P4MycOVMYwGRN02pt234PwHFAJCxE1/Vl48aNO1hXV6fAEj777DPCteuuu44d9w033EDr16/3aQlKv3TpEv8tHS6exXiCvmpqaigWj5NCDqXT/bT9tdfoYnc39yWs5WqXcr6j0rHwK/I+KAy66u7upubmZlq8eLG47mQymeU9PT0fg95UD00lFAptSyQSHNrCgcM6xo8fz2DceOONtHnTJt4v2kXq7LxAHR0d7CvYccujRlNIwchX3WO06ejopM6ODrKsIgP0xy1bGGhhSRgZV7sELaNcRBnclzcwDt4dLAPdAhih+3A4/A8wEKyIAdE0bU0kEuGkDyaGaAo3YwMod999NyvZtCx20JlMf8lDkaK6ICgq8X/sRrxj1QUMwJw/D1BMvu8P99/PYTPCRAHI1Uxf5aLESvQ1FChQPPQKHQvRNG1pNBpdDf2rHl2hHMI3nD592g9tcdy8ppl03eCR3N3VxT5D5n9331U6/2XLUEv2Fe9vsWjRha5uKloWhUMGbdiwnjkVPkVEGWPNUoLnKJB/BdvACqBb6Bg5nbhmGMZWpnBVVWpDodDvw+EQO+H9+/fzDbhx9uzZTC2OU6Te3l5Wms/3AV9R8tCOe9FRSps4pJBdtCh56RKHyfX1DTRnzhx2dgAf/mQ0Iy9ky0jMFi1aVHL+k08+YWWAs4WibrnlFlq+fPmQ/bW2ttJPP/1EW7ZsGbLdiRMn2P/KdT74EfFbYAboGAn2rFlu4qjrGjCoVVVVawqFQiHDCHG0hNwBSKGjhYsWckf5XJ5yHBkJK3AtwPcVgq48y1A0lVRN8Y5Vv72GB1I1DgXzuRw5tsPZLHwJnJ5cdrnSbdq0afTAAw8MAgOybNkyVuqUKVN8yxxJJRa0i204wful0+lBVEwD1sA6hq77+lI8eBVFBQZNqqZpvxMZ97Fjxxg9HONhq6uq2IlnsjkXaU/xLlVppLHCNRck35m759FO0zyHrwpwNB8kvJjt2DS+bjxn/fAloMWRKGY4gWXI8X4luffee5kJ8LsjEQyakVArgEBbYRWyyNQFXUPnQoCFrmnafFwEICgUohEU1tDQQLbtlQXsImmqihyPFMWjI4bbIdUBFam8r5CbCJLi0pU79AjunRzVvU/1ruPFsOHhkO0fOnRoIFu9QtpasGCBv//DDz/Qu+++S2fOnOF3RMSIeh1yIggS3D179pQMhMcee4yTWVEWEgI9wfKEwDHv27dvUPUBx3DecjgvrguQ0Aa6xvMJqgQWuqqqMwXP4SHA4xCMWlGbwYh3exXde0onDwQSICnAhc+riuIn74yh15oR5HMqjyIEDPUN9cynIgS+0rxEKBuOc9u2bczXSG5h+QgiXn31VXrwwQc5t4KffOutt0pCb7QTpaCgUhEJyccoJUH5QfBEqUi0C1q+qBIjg5f6m6Fjlk84H/AekjgcV1VXk+Ol/6Cjih5ciOfkub2iuqA4A5Yi4GMsaaCtYxdpwvgJPh1cKWWBrjCSIaADhJg4J49YKB/hOwCBgnFdBuTRRx8d1O/JkyfZksSAhSBRxiYLAoXnn3/eD1AqvY+okCeTSd96VFWtASBVgtegFNFJyNDdhwTlqKXoO/6oH8BpiKDLvY5+yjSwHcdNOD0KG80kEX5KTBHIIxj7YAMhSNaG+12E5hiwsJyhBP0gIsXAFgOjkgidCwEWuhzNyOk+/Af8BUdRnqpLaojSUen5YSTQGC8gttFw6HIfsI5KRUxQspCuri6aOnXqkP1isCB6Gu4ZOSq9zLxKfj7dcZw+x3Gq0BG4U/wgRhfMXCR//s3Sv25hl52GDw1T0zAIKS5zMSUWbZsLkqMlGJ1QCCwD1dUDBw6UHf1w7hBEdwBEVsrjjz8+yKmDXuCL5HZw6shNhFMXDhu+J+hTyonQuRBgoXsrJqpwDlVesUIC3BaJRlh7hqaxB/B8OXk+2hvtiqi4+2gzpqoHkIi6PJ5TvAQRlFfwKOpCV9eoluORaM6dO5dp4+GHH+aKNWpvUBIsA5EVSkLkRWHBAieOca/s1EVkFHTyACno1L11CEM+o5hhRFAgRWCXdNu2TxWLxQaghYdEZIJ9/J00eTKRbZIaCZPDilcGrMJz0H6465kEY6EKvDwa5PkRhfy4S3HbF7MWJ4ciJA2+8C8RvBzmbwAIBGGqHKoGZceOHX6oLysa5wTlyRIsi4iioezsg/Mj5WhORLCYUZTuO606jnNMOFPkAzB37KNE4BRdSsEmlKX5SR6SQdU77yaFqtfGTQA1r6blZvAaZ/AaX1M4D7FdJ+7Y9O2335aMUnlJzS/ZEOm8+eabw8KJFR9ggmB4e7kSLL3L7yCfl6/h3aHrm266yffhtm0fV23b3i8mR+bPn8+NgBx4NZnsYZ7PZtxMHQBwJq55ZRKpNKJ5inYVrvrZO498v42bteNcNpsjx7G5DI0QFCNytOZG8Bznzp2j5557jvbu3TvoOsrfTzzxBE8vI+TFCB8pXVZSMlUAo9IcPJeP8nmuoQmxbbsVlNViWVbBsqwQHg4ZOhwjlHPkiy9oxR13kJ3P880iKWKK4mxcJHkeiSkDeYbrLRQ/ifTDAcWhXD5Hhby7EqZ1XyuHh6JaUO4lfomgLzwz1gOgYArnLSIfXMO7iOQPx0ePHuUAALOeGBTwIeWeBZNyTz75pF9shd8dDozgOYS6CJqga+l3gEELoiwsd3wvn89vxMOtXLmSXn75ZR6xKKXM6ezkim9vX68/Hy78uVISbXl+Y8C1uDgEEhVMUvVe6iWbHDrXfo6OHT/GeYBY8zVagJBUwkDfcp1M8dZLydVlgCCmIMjL1is9B/oT+YjwfZXAKAeMyGk2btzotykWi8Agyfxgmua/gBiQmzVrFq8iwTFuRljHcTXTWDfPaah+kVHMhahSAdGt6mr+vIjq+ReVR1R3dxf3hQryG2+84U+EyRYyWiJCdvSN3wA4YoKIZ+ekyE6uwoqp5XI0JqItWJhYxXk5YIhKMPIelG1owGqegc4ZENu2d+fz+cNi9m7Tpk0MiEASnGuaFs/2dXRcoGwmw5EUNkVUc0maPfRnEL3pTkXhEjumcTHraBaLXE/CbyBslOP2K3Xo/4tNVra8lQNA3jDgUUuDLjZv3iw780PZbHYP9K0hTvc6OKYoyp9CoZDCixJiMfrqq694FKATOF6Ej7AAHMMpozDII01xfUq5OQwoHY4bnIsySSFf4AVkyAvgs8DBQ43Iq0VGa5EDEk5MiUvW4eTz+ft7e3vP4roMSLvjOBN1XV8CM4TyoUxM6YIzAQJm2VA1TcQTbDHpVIp9S8Es8LFYHIb7+nr7qKu7i3r7+tgqIOfOtdMrr/yHHaMMxtW6eC44+iu1Ce4PBQYWyzU1NfnXsTo+lUr9G8EE1xI//PBDv0NVVaPxePwgFsqJFYrvvPMOT3lCeeBcOEdUSRcvXkS1NdJCOZIrjAOFeeyjxNzW9hFXTGF5oClBVWNlGRCNwkI5VAjuuecevw0WyqVSqd8mk8ks2vCMqQwIuWUDfykplAaFARAAA/qCtXhL7KmurpamT5tOU6ZiKalbagAUuWyOkj1JOtt+1l80IRxr0ImPFTCCUinPKLeUFMoGTWHqWAiWknqrFnkpqZi1HATIqlWrMFk0Nx6P82Jrsb4XieLrr7/O88CinO0MfP8wqGKrDHzk409Xim2sLiWly1hsDdoW0RSCJFFdRlvLss729/c3NzY2fo3gRi7Bl139joZtbW3LHcfZYds2f46AXGTr1q1MO8h+kaNAsZVWi/gZvLeUUvGmbRFJ4IHHsgR9RPBzBGzwwcgzsKpGBq9QKOBzhI0rVqw4Q16RUZaKH+w0Njae3b9//+22bT9lWZb/wQ6iA/wIoqYvv/ySK6siivLXp5aJtsYqNVUSAYao7MLHYmEIyvooQckTWZ4F4ZO2Z9Pp9CNNTU05+ZosZSkrKAcPHsQnbU/H4/ElYgX8/z9pG14kSj+UyWT+vnLlyoNBAF566aWS4xEBIuTTTz/Fcse/RqPRteFwOCy+ExHglFtuea2IHCJ7/qRgmubOfD7/jPfRpz+TOFQYPQiQoUQ4asMw8Fk0FtitCIVCv9F1nT+LVlW16hoFJOU4Tsq2bXwWfdyyrNZCodBSKBSScNgjXsBBRP8FGptkKVwR+ZoAAAAASUVORK5CYII='
TOGGLE_BTN_ON = b'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'


class InterviewGUI:
    def __init__(self):
        self.prompt_window = None
        self.values = None
        self.event = None
        self.audio_input_names = []
        self.show_prompt_window = False
        self.run_code_solver = False
        self.layout = [
            [sg.Text('Audio Source: '), sg.Text('-', key='audio_input_name')],
            [sg.Text('Job Title: '), sg.Text('-', key='job_title')],
            [sg.Text('Company: '), sg.Text('-', key='company')],
            [
                sg.Text('Show Teleprompter: '),
                sg.Button('',
                    image_data=TOGGLE_BTN_ON if self.show_prompt_window == True else TOGGLE_BTN_OFF,
                    key='prompter',
                    button_color=('#323232', '#323232'),
                    border_width=0,
                    metadata={"graphic_off": not self.show_prompt_window}
                )
            ],
            [sg.Text('Tools: '), sg.Button('Code Solver', key='code_solver'), sg.Text(' '), sg.Text('', key='tool_detected_text')],
            [sg.Text('')],
            # [sg.Text('Console Stream', size=(40, 1))],
            # [sg.Output(size=(127, 5), font=('Helvetica 10'))],
            [sg.Text('Console', size=(40, 1))],
            [sg.Text('', size=(120, 5), key='console', expand_x=True, border_width=1, background_color='#1e1e1e')],
            [sg.Text('Questions Detected', size=(40, 1))],
            [sg.Text('', size=(120, 5), key='questions', expand_x=True, border_width=1, background_color='#1e1e1e')],
            [sg.Text('Answers', size=(40, 1))],
            [sg.Text('', size=(120, 6), key='answers', expand_x=True, border_width=1, background_color='#1e1e1e')],
            # [sg.Input(key='-IN-')],
            [
                sg.Button('Exit'),
                sg.Button('Options', visible=False),
                sg.Button('Teleprompter', visible=False)
                # sg.Button('Console'),
                # sg.Button('Questions'),
                # sg.Button('Answers')
            ]
        ]

        self.__window = sg.Window('Your AI Interview Assistant', self.layout, resizable=True, enable_window_config_events=True, icon=ICON)

    def set_audio_input_name(self, value):
        self.__window['audio_input_name'].update(value)

    def set_job_title_name(self, value):
        self.__window['job_title'].update(value)

    def set_company_name(self, value):
        self.__window['company'].update(value)

    def print_console(self, value):
        self.__window['console'].update(value)

    def set_questions(self, value):
        self.__window['questions'].update(value)

    def set_answers(self, value):
        self.__window['answers'].update(value)

    def set_tool_detected_text(self, value):
        self.__window['tool_detected_text'].update(f"{value[0:100]}{'...' if len(value) > 101 else ''}")

    def run_logic(self, blocking=True):
        if blocking:
            timeout = None
        else:
            timeout = 0
        self.event, self.values = self.__window.read(timeout=timeout)
        if self.event in (sg.WIN_CLOSED, 'Exit'):
            return True

        if self.event=='Options':
            self.open_options_dialog(
                'Options',
                'Make a selection for each choice below!',
                ('User 1', 'User 2')
            )

        if self.event=='Teleprompter':
            self.open_prompt_window(
                'Teleprompter',
                []
            )

        if self.event=='Console':
            value = 'adding a console message'
            self.__window['console'].update(value)
            print(value)

        if self.event=='Questions':
            value = 'What is a question?'
            self.__window['questions'].update(value)
            print(value)

        if self.event=='Answers':
            value = 'Answer to the question.'
            self.__window['answers'].update(value)
            print(value)

        if self.event=='prompter':
            self.__window['prompter'].metadata["graphic_off"] = not self.__window['prompter'].metadata["graphic_off"]
            self.show_prompt_window = not self.__window['prompter'].metadata["graphic_off"]
            self.__window['prompter'].update(image_data=TOGGLE_BTN_ON if self.show_prompt_window else TOGGLE_BTN_OFF)
            # Toggle visibility of the prompt window
            if self.show_prompt_window:
                self.show_prompt_window_method() # Renamed for clarity, maps to show_prompt_window
            else:
                self.hide_prompt_window()

        if self.event=='code_solver':
            self.run_code_solver = True
            print('trigger code solver')

        # if self.event=='__WINDOW CONFIG__':
        #     print('WINDOW_CONFIG_EVENT')
            # width, height = self.__window.size
            # console_width = max(20, width // 12)
            # questions_width = max(20, width // 12)
            # answers_width = max(20, width // 12)
            # self.__window['console'].set_size((30, 5))
            # self.__window['questions'].set_size((30, 5))
            # self.__window['answers'].set_size((30, 6))
            # answers = self.__window['answers'].get()
            # self.__window['answers'].update(answers)
            # print()


    def run(self):
        self.run_logic(blocking=False)
        self.__window['Options'].update(visible=True)
        self.__window['Teleprompter'].update(visible=True)
        try:
            while True:  # Event Loop
                if self.run_logic():
                    break
        finally:
             # Ensure prompt window is closed if it exists
            if self.prompt_window and self.prompt_window.TKroot and self.prompt_window.TKroot.winfo_exists():
                self.prompt_window.close()
            self.__window.close()


    def open_options_dialog(self, title, description, options):
        # print(self.values)
        self.audio_input_names = list(options)
        choice, form = sg.Window(title, [
            [sg.T(description)],
            # [sg.T(self.values['-IN-'])],
            [
                sg.Text('Audio Source:', pad=((3, 0), 0)),
                sg.OptionMenu(values=options, expand_x=True, key='input_name_value'),
            ],
            [
                sg.Text('Job Title:', pad=((3, 0), 0)),
                sg.Input(expand_x=True, key='job_title'),
            ],
            [
                sg.Text('Company:', pad=((3, 0), 0)),
                sg.Input(expand_x=True, key='company'),
            ],
            [sg.Text('Resume (optional):', size=(40, 1), pad=((3, 0), 0))],
            [
                sg.Multiline('', size=(120, 4), key='resume', pad=((3, 0), 0), no_scrollbar=True),
            ],
            # [sg.Text('')],
            [sg.OK(s=10), sg.Cancel(s=10)]
        ], disable_close=True, size=(300, 200), icon=ICON).read(close=True)
        return choice, form

    def open_prompt_window(self, title, answer_stream):
        self.prompt_window = sg.Window(title, [
            [sg.Multiline('', font=('Arial', 20, 'bold'), size=(
            500, 11), key='prompt', border_width=1, background_color='#1e1e1e')],
            [sg.OK(button_text='Continue', s=10)]
        ], disable_close=False, size=(500, 300), icon=ICON)
        self.prompt_window.read(close=False, timeout=0)
        self.prompt_window['prompt'].update(disabled=True)
        report = []
        for resp in answer_stream:
            if resp.choices and resp.choices[0].delta:
                stream_text = resp.choices[0].delta.content if resp.choices[0].delta.content else ''
                report.append(stream_text)
                result = "".join(report).strip()
                result = result.replace("\n", "")
                # print(f"\r{result}", end='')
                self.prompt_window['prompt'].update(f"{result}")
                self.prompt_window.read(close=False, timeout=0)
        result = "".join(report).strip()
        result = result.replace("\n", "")
        self.set_answers(f"{result}")
        choice, form = self.prompt_window.read(close=True)
        return choice, form

    def markdown_to_rich_text(self, text):
        text = re.sub(r'\*\*(.*?)\*\*', r'[BOLD]\1[/BOLD]', text)
        text = re.sub(r'\*(.*?)\*', r'[ITALIC]\1[/ITALIC]', text)
        text = re.sub(r'`([^`]+)`', r'[CODE]\1[/CODE]', text)
        text = re.sub(r'```(.*?)```', r'[CODEBLOCK]\1[/CODEBLOCK]', text, flags=re.DOTALL)
        formatted_text = text.replace("[BOLD]", "").replace("[/BOLD]", "")
        formatted_text = formatted_text.replace("[ITALIC]", "").replace("[/ITALIC]", "")
        formatted_text = formatted_text.replace("[CODE]", "`").replace("[/CODE]", "`")
        formatted_text = formatted_text.replace("[CODEBLOCK]", "```\n").replace("[/CODEBLOCK]", "\n```")
        return formatted_text

    def _create_prompt_window(self):
        """Creates the reusable prompt window."""
        if self.prompt_window is None or self.prompt_window.TKroot is None or self.prompt_window.TKroot.winfo_exists() == 0:
            self.prompt_window = sg.Window(
                'Prompt', # Default title, will be updated
                [
                    [sg.Multiline('', font=('Arial', 16, 'bold'), size=(800, 15), key='prompt', border_width=1, wrap_lines=True, background_color='#1e1e1e')],
                    [sg.Image(data=None, key='image')],
                    # [sg.OK(button_text='Continue', s=10)] # Consider removing or disabling OK if not needed for reuse
                ],
                disable_close=True, # Keep True to prevent accidental closing
                finalize=True,      # Finalize to allow updates before first read
                size=(800, 320),
                resizable=True,
                icon=ICON,
                alpha_channel=0.7,
                keep_on_top=True,
                location=(0, 0),
                no_titlebar=False, # Ensure titlebar is present for title updates
                grab_anywhere=True # Allow moving window easily
            )
            self.prompt_window.hide() # Start hidden
            self.prompt_window.read(timeout=0) # Initial read to finalize layout
            self.prompt_window['prompt'].update(disabled=True) # Keep disabled for display

    def update_prompt_window(self, title, answer_stream):
        """Updates and shows the reusable prompt window."""
        self._create_prompt_window() # Ensure window exists

        self.prompt_window.set_title(title)
        self.prompt_window['prompt'].update('') # Clear previous content
        self.prompt_window.un_hide()
        self.prompt_window.bring_to_front()

        report = []
        for resp in answer_stream:
            # Check if window still exists before updating
            if self.prompt_window is None or self.prompt_window.TKroot is None or self.prompt_window.TKroot.winfo_exists() == 0:
                print("Prompt window closed unexpectedly during stream.")
                break # Exit loop if window closed

            if resp.choices and resp.choices[0].delta:
                stream_text = resp.choices[0].delta.content if resp.choices[0].delta.content else ''
                report.append(stream_text)
                result = "".join(report)
                formatted_text = self.markdown_to_rich_text(result) # Use existing markdown helper
                try:
                    self.prompt_window['prompt'].update(formatted_text)
                    # Read with timeout to keep window responsive and check for events (like manual close if disable_close=False)
                    event, values = self.prompt_window.read(timeout=10)
                    if event == sg.WIN_CLOSED or event == 'Continue': # Handle potential close/continue events
                        # If we want 'Continue' to hide the window:
                        # self.hide_prompt_window()
                        # break # Or just break the stream loop
                        pass # For now, just keep updating
                except Exception as e:
                    print(f"Error updating prompt window: {e}")
                    break # Stop streaming on error

        result = "".join(report).strip()
        self.set_answers(f"{result}") # Update main window answers

        # Decide what happens after streaming finishes. Hide? Wait for 'Continue'?
        # For now, let's assume it stays open until explicitly hidden or closed.
        # event, values = self.prompt_window.read() # Blocking read if we need user interaction
        # if event == 'Continue' or event == sg.WIN_CLOSED:
        #     self.hide_prompt_window()

        return # No return needed like the old method

    def hide_prompt_window(self):
        """Hides the reusable prompt window if it exists."""
        if self.prompt_window and self.prompt_window.TKroot and self.prompt_window.TKroot.winfo_exists():
            self.prompt_window.hide()

    def show_prompt_window_method(self): # Renamed to avoid conflict with instance variable
        """Shows the reusable prompt window if it exists."""
        # Ensure window is created if it wasn't already (e.g., toggled on before first use)
        self._create_prompt_window()
        if self.prompt_window and self.prompt_window.TKroot and self.prompt_window.TKroot.winfo_exists():
            self.prompt_window.un_hide()
            self.prompt_window.bring_to_front()


    # --- Old open_prompt_window2 method removed ---
    # def open_prompt_window2(self, title, answer_stream):
    #     # window = webview.create_window('Code Solver', None, '<html><body></body></html>')
    #     self.prompt_window = sg.Window(
    #         title,
    #         [
    #             [sg.Multiline('', font=('Arial', 16, 'bold'), size=(800, 13), key='prompt', border_width=1, wrap_lines=True, background_color='#1e1e1e')],
    #             [sg.Image(data=None, key='image')],
    #             [sg.OK(button_text='Continue', s=10)]
    #         ],
    #         disable_close=True,
    #         size=(800, 320),
    #         resizable=True,
    #         icon=ICON,
    #         alpha_channel=0.7,  # Set transparency
    #         keep_on_top=True,   # Keep window above others
    #         location=(0, 0)     # Position at top-left corner
    #     )
    #     self.prompt_window.read(close=False, timeout=0)
    #     self.prompt_window['prompt'].update(disabled=True)
    #     report = []
    #     for resp in answer_stream:
    #         if resp.choices and resp.choices[0].delta:
    #             stream_text = resp.choices[0].delta.content if resp.choices[0].delta.content else ''
    #             report.append(stream_text)
    #             result = "".join(report)
    #             formatted_result = result.replace("\n", "\n")
    #             # formatted_markdown = markdown.markdown(formatted_result)
    #             formatted_text = self.markdown_to_rich_text(formatted_result)
    #             self.prompt_window['prompt'].update(formatted_text)
    #             # window.html = formatted_markdown
    #             self.prompt_window.read(close=False, timeout=0)
    #     result = "".join(report).strip()
    #     result = result.replace("\n", "")
    #     self.set_answers(f"{result}")
    #     # webview.start()
    #     # choice, form = self.prompt_window.read(close=True)
    #     return #choice, form


if __name__=="__main__":
    # options = ('User 1', 'User 2')
    # Create the class
    my_gui = InterviewGUI()
    # run the event loop
    my_gui.run()
    #
    # while True:
    #     event, value = window.read()  # timeout=0
    #     handler.handle_event(event, value)
