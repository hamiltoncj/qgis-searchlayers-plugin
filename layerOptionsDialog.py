"""
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os

from qgis.PyQt.uic import loadUiType
from qgis.PyQt.QtWidgets import QDialog, QListWidgetItem
from qgis.PyQt.QtCore import Qt, QCoreApplication

from qgis.core import QgsProject, QgsVectorLayer


def tr(string):
    return QCoreApplication.translate('@default', string)


FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'layerOptionsDialog.ui'))

SEARCHLAYERS_SCOPE = 'SearchLayers'
DISABLED_LAYER_IDS_KEY = 'disabledLayerIds'


def getDisabledLayerIds():
    '''Return the set of vector layer ids excluded from search.'''
    ids, ok = QgsProject.instance().readListEntry(SEARCHLAYERS_SCOPE, DISABLED_LAYER_IDS_KEY)
    if ok:
        return set(ids)
    return set()


def setDisabledLayerIds(layer_ids):
    '''Persist the excluded layer ids with the current QGIS project.'''
    QgsProject.instance().writeEntry(SEARCHLAYERS_SCOPE, DISABLED_LAYER_IDS_KEY, list(layer_ids))


def isSearchableLayer(layer, disabled_ids=None):
    '''True if the layer is a vector layer that should be searched and listed.'''
    if not isinstance(layer, QgsVectorLayer):
        return False
    if layer.sourceName().startswith('__'):
        return False
    if disabled_ids is None:
        disabled_ids = getDisabledLayerIds()
    return layer.id() not in disabled_ids


class LayerOptionsDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(LayerOptionsDialog, self).__init__(parent)
        self.setupUi(self)
        self.selectAllButton.clicked.connect(lambda: self.setAllChecked(True))
        self.deselectAllButton.clicked.connect(lambda: self.setAllChecked(False))
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.populateLayerList()

    def populateLayerList(self):
        '''List project vector layers in legend order, checked if searchable.'''
        self.layerListWidget.clear()
        disabled_ids = getDisabledLayerIds()
        for tree_layer in QgsProject.instance().layerTreeRoot().findLayers():
            layer = tree_layer.layer()
            if not isinstance(layer, QgsVectorLayer):
                continue
            if layer.sourceName().startswith('__'):
                continue
            item = QListWidgetItem(layer.name())
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            if layer.id() in disabled_ids:
                item.setCheckState(Qt.CheckState.Unchecked)
            else:
                item.setCheckState(Qt.CheckState.Checked)
            item.setData(Qt.ItemDataRole.UserRole, layer.id())
            self.layerListWidget.addItem(item)

    def setAllChecked(self, checked):
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for i in range(self.layerListWidget.count()):
            self.layerListWidget.item(i).setCheckState(state)

    def accept(self):
        disabled = []
        for i in range(self.layerListWidget.count()):
            item = self.layerListWidget.item(i)
            if item.checkState() != Qt.CheckState.Checked:
                disabled.append(item.data(Qt.ItemDataRole.UserRole))
        setDisabledLayerIds(disabled)
        super(LayerOptionsDialog, self).accept()
