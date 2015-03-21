__author__ = 'Nixon'


from kivy.uix.gridlayout import GridLayout
from kivy.base import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.listview import ListView, ListItemLabel
from kivy.adapters.listadapter import ListAdapter
import database_interface
import re

Builder.load_file('../Kivy_Layouts/AlertScreen.kv')


class AlertScreen(Screen):
    pass


class AlertGrid(GridLayout):
    pass


class MessagesList(ListView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        concerns = database_interface.get_data(database_interface.DETECTED_CONCERNS)
        msgs = list()
        msgs.append(" ")

        if len(concerns) != 0:
            concerns = concerns[0]['info']
            for msg in concerns:
                msgs.append(re.sub("(.{60})", "\\1\n", msg['message']['plain'], 0, re.DOTALL))

        list_item_args_converter = lambda row_index, text: {
            'text': text,
            'height': 50,
            'font_size': 20
        }

        self.adapter = ListAdapter(data=msgs,
                                   args_converter=list_item_args_converter,
                                   cls=ListItemLabel)