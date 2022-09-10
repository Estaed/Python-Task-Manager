#!/usr/bin/env python
import sys
from PySimpleGUI.PySimpleGUI import execute_subprocess_still_running
if sys.version_info[0] >= 3:
    import PySimpleGUI as sg
else:
    import PySimpleGUI27 as sg
import os
import signal
import psutil
import operator

GRAPH_WIDTH = 120
GRAPH_HEIGHT = 40
TRANSPARENCY = 1 
NUM_COLS = 4
POLL_FREQUENCY = 100

colors = ('#23a0a0', '#56d856', '#be45be', '#5681d8', '#d34545', '#BE7C29')

"""
    Calisan Processleri Gormeye yarayan, CPU Kullanimina Gore Siralayabildigimiz.
    Psutil Kutuphanesi ile hazirlanan bir uygulama
"""


def kill_proc_tree(pid, sig=signal.SIGTERM, include_parent=True,
                   timeout=None, on_terminate=None):

    if pid == os.getpid():
        raise RuntimeError("Olmeyi Reddediyorum")
    parent = psutil.Process(pid)
    children = parent.children(recursive=True)
    if include_parent:
        children.append(parent)
    for p in children:
        p.send_signal(sig)
    gone, alive = psutil.wait_procs(children, timeout=timeout,
                                    callback=on_terminate)
    return (gone, alive)


def main():

    # ----------------  Form Olusturma  ----------------
    sg.ChangeLookAndFeel('Topanga')

    layout = [[sg.Text('Task Manager - Bir veya birden fazla process secin',
                       size=(45, 1), font=('Helvetica', 15), text_color='red')],
              [sg.Text('    PID         CPU      THR    NAME',
              size=(30, 1), font=('Helvetica', 10), text_color='yellow')],
              [sg.Listbox(values=[' '], size=(50, 30), select_mode=sg.SELECT_MODE_EXTENDED,  font=(
                  'Courier', 12), key='_processes_')],
              [sg.Text(
                  'Bir veya iki defa sayfayi yenileyin. Ilki processler icin, ikincisi CPU kullanimlari icin')],
              [sg.T('Isme Gore Filtrele', font='ANY 14'), sg.In(
                  size=(15, 1), font='any 14', key='_filter_'),sg.RButton('CPU Grafik', button_color=("black","white"))],
              [sg.RButton('Isme gore', ),
               sg.RButton("CPU'a Gore ", button_color=(
                   'white', 'DarkOrange2')),
               sg.RButton('Thread ile CPU', button_color=('white', 'Black')),
               sg.RButton('Oldur', button_color=(
                   'white', 'red'), bind_return_key=True),
               sg.RButton('Olustur', button_color=('white', 'green'), bind_return_key=True)]]

    window = sg.Window('Task Manager',
                       keep_on_top=True,
                       auto_size_buttons=False,
                       default_button_element_size=(12, 1),
                       return_keyboard_events=True,
                       ).Layout(layout)

    display_list = None
    # ---------------- Ana Dongu  ----------------
    while (True):
        # --------- Oku ve Pencereyi Guncelle --------
        button, values = window.Read()

        if 'Mouse' in button or 'Control' in button or 'Shift' in button:
            continue
        # --------- Buton islemlerini yap --------
        if values is None or button == 'Exit':
            break

        if button == 'Isme gore':
            psutil.cpu_percent(interval=None)
            procs = psutil.process_iter()
            all_procs = [[proc.cpu_percent(), proc.name(), proc.pid, proc.num_threads()]
                         for proc in procs]
            sorted_by_cpu_procs = sorted(
                all_procs, key=operator.itemgetter(1), reverse=False)
            display_list = []
            for process in sorted_by_cpu_procs:
                display_list.append('{:5d} {:5.2f} {} {}\n'.format(
                    process[2], process[0]/10, process[3], process[1]))
            window.FindElement('_processes_').Update(display_list)
            

        elif button == "CPU'a Gore ":
            psutil.cpu_percent(interval=None)
            procs = psutil.process_iter()
            all_procs = [[proc.cpu_percent(), proc.name(), proc.pid, proc.num_threads()]
                         for proc in procs]
            sorted_by_cpu_procs = sorted(
                all_procs, key=operator.itemgetter(0), reverse=True)
            display_list = []
            for process in sorted_by_cpu_procs:
                display_list.append('{:5d} {:5.2f} {} {}\n'.format(
                    process[2], process[0]/10, process[3], process[1]))
            window.FindElement('_processes_').Update(display_list)

        # n_thread sayisila cpu oranlayip ona gore siralayacak
        elif button == "Thread ile CPU":
            psutil.cpu_percent(interval=None)
            procs = psutil.process_iter()
            all_procs = [[proc.cpu_percent(), proc.name(), proc.pid, proc.num_threads()]
                         for proc in procs]
            sorted_by_cpu_procs = sorted(
                all_procs, key=operator.itemgetter(0), reverse=False)
            display_list = []
            for process in sorted_by_cpu_procs:
                display_list.append('{:5d} {:5.2f} {} {}\n'.format(
                    process[2], process[0]/10, process[3], process[1]))
            window.FindElement('_processes_').Update(display_list)

        elif button == 'Oldur':
            processes_to_kill = values['_processes_']
            for proc in processes_to_kill:
                pid = int(proc[0:5])
                if sg.PopupYesNo('{} {} Oldurulmek Ister misin?'.format(pid, proc[13:]), keep_on_top=True) == 'Yes':
                    kill_proc_tree(pid=pid)
        
        elif button == 'Olustur':
            create_psutil = sg.popup_get_text("exe programin ismini giriniz: ", keep_on_top = True)
            if sg.popup_get_text("exe programin ismini giriniz: ", keep_on_top = True) == "Ok":
                print(create_psutil)                  
            
#-------------------------------------------------------------------------------------------------------------------------------------
        elif button == "CPU Grafik":

            class DashGraph(object):
                def __init__(self, graph_elem, text_elem, starting_count, color):
                    self.graph_current_item = 0
                    self.graph_elem = graph_elem
                    self.text_elem = text_elem
                    self.prev_value = starting_count
                    self.max_sent = 1
                    self.color = color
                    self.line_list = []

                def graph_percentage_abs(self, value):
                    self.line_list.append(self.graph_elem.draw_line(
                        (self.graph_current_item, 0),
                        (self.graph_current_item, value),
                        color=self.color))
                    if self.graph_current_item >= GRAPH_WIDTH:
                        self.graph_elem.move(-1,0)
                        self.graph_elem.delete_figure(self.line_list[0])
                        self.line_list = self.line_list[1:]
                    else:
                        self.graph_current_item += 1

                def text_display(self, text):
                    self.text_elem.update(text)

            def main(location):
                def Txt(text, **kwargs):
                    return(sg.Text(text, font=('Helvetica 8'), **kwargs))

                def GraphColumn(name, key):
                    return sg.Column([[Txt(name, size=(10,1), key=('-TXT-', key))],
                                    [sg.Graph((GRAPH_WIDTH, GRAPH_HEIGHT), (0, 0), (GRAPH_WIDTH, 100), background_color='black', key=('-GRAPH-', key))]], pad=(2, 2))

                num_cores = len(psutil.cpu_percent(percpu=True))

                sg.theme('Black')

                layout = [[sg.Text('     CPU Kullanimi')] ]

                for rows in range(num_cores//NUM_COLS+1):
                    layout += [[GraphColumn('CPU '+str(rows*NUM_COLS+cols), (rows, cols)) for cols in range(min(num_cores-rows*NUM_COLS, NUM_COLS))]]

                window = sg.Window('CPU Kullanimi Grafigi', layout,
                                keep_on_top=True,
                                grab_anywhere=True,
                                no_titlebar=False,
                                return_keyboard_events=True,
                                alpha_channel=TRANSPARENCY,
                                use_default_focus=False,
                                finalize=True,
                                margins=(1,1),
                                element_padding=(0,0),
                                border_depth=0,
                                location=location)


                graphs = []
                for rows in range(num_cores//NUM_COLS+1):
                    for cols in range(min(num_cores-rows*NUM_COLS, NUM_COLS)):
                        graphs += [DashGraph(window[('-GRAPH-', (rows, cols))],
                                            window[('-TXT-',  (rows, cols))],
                                            0, colors[(rows*NUM_COLS+cols)%len(colors)])]

                while True :
                    event = window.read(timeout=POLL_FREQUENCY)
                    if event in (sg.WIN_CLOSED, 'Exit'):
                        break
                    stats = psutil.cpu_percent(percpu=True)

                    for i, util in enumerate(stats):
                        graphs[i].graph_percentage_abs(util)
                        graphs[i].text_display('{} CPU {:2.0f}'.format(i+1, util))

                window.close()

            if __name__ == "__main__":
                
                if len(sys.argv) > 1:
                    location = sys.argv[1].split(',')
                    location = (int(location[0]), int(location[1]))
                else:
                    location = (None, None)
                main(location)
#--------------------------------------------------------------------------------------------------------------------------------------
        else:
            if display_list is not None:
                new_output = []
                for line in display_list:
                    if values['_filter_'] in line.lower():
                        new_output.append(line)
                window.FindElement('_processes_').Update(new_output)


if __name__ == "__main__":
    main()
