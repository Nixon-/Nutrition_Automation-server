__author__ = 'Nixon'

from kivy.uix.gridlayout import GridLayout
from kivy.base import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.listview import ListView, ListItemLabel
from kivy.adapters.listadapter import ListAdapter
import Report

Builder.load_file('Kivy_Layouts/ReportScreen.kv')


def normalize(line, separator=' '):
    while len(line) < 50:
        line += separator
    return line


class ReportScreen(Screen):
    pass


class ReportGrid(GridLayout):
    pass


class ReportLowerGrid(GridLayout):
    def update(self):
        self.clear_widgets()
        self.add_widget(ReportView())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update()


class ReportView(ListView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        report = Report.generate_consumption_report(8, hours=1)
        document = list()
        for section in report:
            document.append('=' * 40)
            document.append('Area: ' + str(section['bin']))
            document.append('Name: ' + str(section['name']).capitalize())
            document.append('Type: ' + str(section['type']).capitalize())
            if section['date of purged'] is None:
                document.append('Purged: No')
            else:
                document.append('Purged: Yes (' +
                                section['date of purged'].strftime('%H:%M %a %d/%b') + " )")
            document.append('=' * 40)

            def print_consumption(con, title):
                document.append('-' * 30)
                document.append(title.capitalize())
                document.append('-' * 30)
                if len(con) == 0 or con is None:
                    document.append('( No data )')
                    return
                if title == "hourly":
                    fmt = '%H:%M %a %d/%b'
                else:
                    fmt = '%a %d/%b'
                for decade in con:
                    document.append(decade['start time'].strftime(fmt) + ' to ' +
                                    decade['end time'].strftime(fmt))
                    document.append('Decrease: ' + "{0:.2f}".format(decade['decrease']))
                    document.append('Increase: ' + "{0:.2f}".format(decade['increase']))
                    document.append('Difference: ' + "{0:.2f}".format(decade['difference']))
                    document.append('-'*20)
                document.pop()

            if 'hourly' in section['consumption']:
                print_consumption(section['consumption']['hourly'], 'hourly')

            if 'daily' in section['consumption']:
                print_consumption(section['consumption']['daily'], 'daily')

            if 'weekly' in section['consumption']:
                print_consumption(section['consumption']['weekly'], 'weekly')

            if 'monthly' in section['consumption']:
                print_consumption(section['consumption']['monthly'], 'monthly')

        list_adapter = ListAdapter(data=document, cls=ReportLine)
        self.adapter = list_adapter


class ReportLine(ListItemLabel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_size = 30
        self.height = 40
        self.padding = (10, 10)
