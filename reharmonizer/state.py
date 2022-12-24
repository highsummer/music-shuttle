commandline = None

class state:
    singables = []

def append_commandline(text):
    commandline.write(text)


class Node:
    def __init__(self):
        self.selected = False
        self.children = []
        self.identifier = None


class SingableNode(Node):
    id_num = 0
    def __init__(self, func, *args, **kwargs):
        super(SingableNode, self).__init__()
        self.descendant = None
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.identifier = 'sing:' + str(SingableNode.id_num)
        SingableNode.id_num += 1
    
    def apply(self):
        if isinstance(self.descendant, (list, tuple)):
            applied = [d.apply() for d in self.descendant]
        else:
            applied = self.descendant.apply()
        return self.func(*self.args, **self.kwargs)(applied)


from singable import Parallel

class PianoRollNode(SingableNode):
    def __init__(self):
        super(PianoRollNode, self).__init__(None)
        self.keys = []

    def apply(self):
        return Parallel()(self.keys)


class KeyNode(Node):
    id_num = 0
    def __init__(self, key):
        super(KeyNode, self).__init__()
        self.key = key
        self.identifier = 'key:' + str(KeyNode.id_num)
        KeyNode.id_num += 1


from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QLineEdit
from PyQt5.QtCore import Qt
from PyQt5.Qt import QPainter


class Draggable(QWidget):
    def __init__(self, *args, **kwargs):
        # QWidget.__init__(self, *args, **kwargs)
        self._previous_pos = QPoint(0, 0)
        self.setMouseTracking(True)
    
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._previous_pos = e.pos()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton:
            dpos = e.pos() - self._previous_pos
            self.dragEvent(e, dpos)
            self._previous_pos = e.pos()
    
    def dragEvent(self, e, dpos):
        self.move(self.pos() + dpos)



class NodeTarget(QWidget):
    def __init__(self, node, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        self.node = node
        self.setMouseTracking(True)
    
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            append_commandline(self.node.identifier)


class QSingableNode(QLabel, NodeTarget):
    def __init__(self, singable, *args, **kwargs):
        QLabel.__init__(self, *args, **kwargs)
        NodeTarget.__init__(self, singable, *args, **kwargs)
        self.setMouseTracking(True)
        self.setStyleSheet('background-color: orange')
        self.setText(singable.identifier)
        self.setGeometry(0, 0, 100, 80)
        self.singable = singable
    
    


class QKey(QLabel, NodeTarget):
    def __init__(self, kn, *args, unit_length=20, unit_height=16, number_offset=48, **kwargs):
        QLabel.__init__(self, *args, **kwargs)
        NodeTarget.__init__(self, kn, parent=kwargs['parent'])
        self.setStyleSheet('background-color: cyan')
        key = kn.key
        self.setText(key.note.tone)
        self.setGeometry(key.start * unit_length, -(key.note.midi_number() - number_offset) * unit_height, key.length * unit_length, unit_height)



# class ContainerNodeEditor(QWidget):
class ContainerNodeEditor(QLabel):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        self.setGeometry(0, 360, 1280, 240)
        self.setObjectName('node_editor')
        self.setStyleSheet('background-color: red;')


class ContainerNodes(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        self.setGeometry(0, 0, 1280, 360)
        self.setObjectName('nodes')


class Form(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        self.setFixedSize(1280, 720)
        self.drawfuncs = []
        self.painter = QPainter()
        self.container_node_editor = ContainerNodeEditor(parent=self)
        self.container_nodes = ContainerNodes(parent=self)
        self.container_command_line = QCommandLine(parent=self)
        global commandline
        commandline = self.container_command_line
    
    def paintEvent(self, e):
        self.painter.begin(self)
        for func in self.drawfuncs:
            func(self.painter)
        self.painter.end()

    def clear(self):
        self.painter.begin(self)
        self.painter.eraseRect(0, 0, 1280, 720)
        self.painter.end()
        self.hide()

        self.container_node_editor.close()
        self.container_nodes.close()

        self.container_node_editor = ContainerNodeEditor(parent=self)
        self.container_nodes = ContainerNodes(parent=self)

        self.drawfuncs = []
        self.update()
        # form.show()


class QNodeEditor(QWidget):
    def __init__(self, target, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        self.setGeometry(0, 0, 1280, 240)
        self.target = target

    def draw(self):
        pass


class QPianoRoll(QNodeEditor, Draggable):
    def __init__(self, *args, **kwargs):
        QNodeEditor.__init__(self, *args, **kwargs)
        Draggable.__init__(self, *args, **kwargs)
        number_max = max([kn.key.note.midi_number() for kn in self.target.keys])
        number_min = min([kn.key.note.midi_number() for kn in self.target.keys])
        for kn in self.target.keys:
            w = QKey(kn, parent=self, number_offset=(number_max + number_min) / 2)
            w.move(w.pos() + QPoint(0, self.height() / 2))
    
    def dragEvent(self, e, dpos):
        for c in self.children():
            c.move(c.pos() + dpos)


from shlex import split

class QCommandLine(QWidget):

    class QCommandLineEdit(QLineEdit):
        def __init__(self, *args, **kwargs):
            QLineEdit.__init__(self, *args, **kwargs)
            self.setGeometry(0, 96, 1280, 24)

        def keyPressEvent(self, e):
            QLineEdit.keyPressEvent(self, e)
            if e.key() == Qt.Key_Return:
                self.parent().history.push(self.text())
                self.parent().command(self.text())
                self.clear()

    class QCommandLineHistory(QLabel):
        def __init__(self, *args, **kwargs):
            QLabel.__init__(self, *args, **kwargs)
            self.setGeometry(0, 0, 1280, 24 * 4)
            self.setStyleSheet('background-color: gray')
            self.texts = []
        
        def push(self, text):
            self.texts.append(text)
            self.setText('\n'.join(self.texts[-4:]))

    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        self.text = self.QCommandLineEdit(parent=self)
        self.history = self.QCommandLineHistory(parent=self)
        self.setGeometry(0, 600, 1280, 120)
        self.setObjectName('command_line')
    
    def write(self, text):
        if self.text.text():
            self.text.setText(self.text.text() + ' ' + text)
        else:
            self.text.setText(text)
    
    def command(self, raw_cmd):
        cmd = split(raw_cmd)
        if cmd[0] == 'redraw':
            redraw()
        
        elif cmd[0] == 'delete':
            if cmd[1].startswith('sing:'):
                node = find_node(state, cmd[1])
                state.singables.remove(node)
                for s in state.singables:
                    if isinstance(s.descendant, (list, tuple)):
                        s.descendant.remove(node)
                    if s.descendant is node:
                        s.descendant = None
                redraw()
        
        elif cmd[0] == 'create':
            if cmd[1] == 'sing':
                state.singables.append(SingableNode(Repeat, 16))

        elif cmd[0] == 'rename':
            node = find_node(state, cmd[1])
            node.identifier = cmd[2]
            redraw()
        
        elif cmd[0] == 'stop':
            print('stopped')


def find_node(state, identifier):
    try:
        return next((s for s in state.singables if s.identifier == identifier))
    except StopIteration:
        pass

    try:
        for s in state.singables:
            if isinstance(s, PianoRollNode):
                return next((kn for kn in s.keys if kn.identifier == identifier))
    except StopIteration:
        pass
    
    raise ValueError('No such node {}'.format(identifier))


from math import pi, cos, sin
from PyQt5.QtCore import QPoint

def draw(form, state):

    form.clear()

    def group_sort(nodes):
        # Copy connection information into dictionary
        connections = {}
        for n in nodes:
            descendant = n.descendant
            if descendant is None:
                descendant = []
            elif isinstance(descendant, tuple):
                descendant = list(descendant)
            elif not isinstance(descendant, list):
                descendant = [descendant]
            connections[n] = descendant
        # Sorting helper function
        def _group_sort():
            while connections:
                # Select nodes to pull out
                out = [n for n in connections.keys() if not connections[n]]
                # Return the nodes
                yield out[:]
                # Remove nodes from connection information
                for n in connections.keys():
                    for m in out:
                        if m in connections[n]:
                            connections[n].remove(m)
                # Remove nodes from node list
                while out:
                    m = out.pop()
                    del connections[m]
        # Returned nodes are reversed in order
        return list(reversed(list(_group_sort())))

    ordering = group_sort(state.singables)

    widgets = {}

    dx = 100
    for group in ordering:
        dy = 100
        for s in group:
            w = QSingableNode(s, parent=form.container_nodes)
            w.move(dx, dy)
            widgets[s] = w
            dy += 100
        dx += 120

    def draw_node_lines(painter):
        for s in state.singables:
            descendants = s.descendant
            if not descendants:
                continue
            if not isinstance(descendants, (list, tuple)):
                descendants = [descendants]
            for d in descendants:
                w1 = widgets[s]
                w2 = widgets[d]
                painter.drawLine(w1.pos() + QPoint(w1.width(), w1.height() / 2), w2.pos() + QPoint(0, w2.height() / 2))
    
    
    QPianoRoll(find_node(state, 'sing:melody'), parent=form.container_node_editor)

    form.drawfuncs.append(draw_node_lines)
    form.update()
    form.show()


def play(target):
    from instruments.piano import acoustic_grand_piano
    from instruments.bass import synth_bass_1
    from instruments.drum_kits import standard_drum_kit
    from singable import to_midi

    song = target.apply()
    mid = to_midi(song, instruments={ 
        0: acoustic_grand_piano,
        1: acoustic_grand_piano,
        2: synth_bass_1,
        9: standard_drum_kit
    })
    mid.save('new_song.mid')

    # import os
    # import subprocess
    # FNULL = open(os.devnull, 'w')
    # subprocess.call(['timidity', 'new_song.mid'], stdout=FNULL, stderr=subprocess.STDOUT)

    import mido
    port = mido.open_output()
    for msg in mid.play():
        port.send(msg)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    form = Form()

    from songs import crepas_song, crepas_scale
    s = PianoRollNode()
    s.keys = list((KeyNode(k) for k in crepas_song.sing() if k.note))
    s.identifier = 'sing:melody'
    state.singables.append(s)
    
    from singable import Reharmonize
    s = SingableNode(Reharmonize, crepas_scale)
    s.identifier = 'sing:reharmonize'
    state.singables.append(s)

    from riffs import riff1
    s = PianoRollNode()
    s.keys = list((KeyNode(k) for k in riff1.sing() if k.note))
    s.identifier = 'sing:baseriff'
    state.singables.append(s)

    from singable import Arpeggio
    s = SingableNode(Arpeggio)
    s.identifier = 'sing:arp'
    state.singables.append(s)

    from singable import Repeat
    s = SingableNode(Repeat, 16)
    s.identifier = 'sing:repeat'
    state.singables.append(s)

    from singable import Transpose
    from note import Interval
    s = SingableNode(Transpose, Interval('-P8'))
    s.identifier = 'sing:transpose'
    state.singables.append(s)

    from singable import Parallel
    s = SingableNode(Parallel)
    s.identifier = 'sing:parallel'
    state.singables.append(s)

    find_node(state, 'sing:reharmonize').descendant = find_node(state, 'sing:melody')
    find_node(state, 'sing:repeat').descendant = find_node(state, 'sing:baseriff')
    find_node(state, 'sing:arp').descendant = (find_node(state, 'sing:reharmonize'), find_node(state, 'sing:repeat'))
    find_node(state, 'sing:transpose').descendant = find_node(state, 'sing:arp')
    find_node(state, 'sing:parallel').descendant = [find_node(state, 'sing:melody'), find_node(state, 'sing:transpose')]

    draw(form, state)
    # form.show()
    # play(find_node(state, 'parallel'))

    def redraw():
        draw(form, state)

    exit(app.exec_())