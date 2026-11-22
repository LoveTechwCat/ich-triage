import http.server
import json
import socket
import threading
import time

import qt

import slicer
from slicer.i18n import tr as _
from slicer.ScriptedLoadableModule import (
    ScriptedLoadableModule,
    ScriptedLoadableModuleLogic,
    ScriptedLoadableModuleTest,
    ScriptedLoadableModuleWidget,
)

from ICHTriageLib import monai_label

#
# ICHTriage
#


class ICHTriage(ScriptedLoadableModule):
    """Module description for Slicer's module list.

    Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("ICH Triage")
        self.parent.categories = ["ICH"]
        self.parent.dependencies = []
        self.parent.contributors = ["LoveTechwCat (ich-triage)"]
        self.parent.helpText = _("""
Radiologist module of the ICH (intracerebral hemorrhage) AI triage system.
This first version only stores the server settings and checks the connection to a MONAI Label server.
See <a href="https://github.com/LoveTechwCat/ich-triage/tree/main/services/slicer-ich-triage">the module README</a>.
""")
        self.parent.acknowledgementText = _("""
Built on the 3D Slicer scripted module template (Extension Wizard).
""")


#
# ICHTriageWidget
#


class ICHTriageWidget(ScriptedLoadableModuleWidget):
    """Module panel.

    Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None) -> None:
        ScriptedLoadableModuleWidget.__init__(self, parent)
        self.logic = None

    def setup(self) -> None:
        ScriptedLoadableModuleWidget.setup(self)

        uiWidget = slicer.util.loadUI(self.resourcePath("UI/ICHTriage.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)
        uiWidget.setMRMLScene(slicer.mrmlScene)

        self.logic = ICHTriageLogic()

        self.ui.serverUrlLineEdit.placeholderText = monai_label.DEFAULT_SERVER_URL
        self.ui.pacsUrlLineEdit.placeholderText = "http://pacs:8080/dcm4chee-arc/aets/DCM4CHEE/rs"
        self.ui.serverUrlLineEdit.text = self.logic.serverUrl()
        self.ui.pacsUrlLineEdit.text = self.logic.pacsUrl()

        self.ui.serverUrlLineEdit.connect("editingFinished()", self.onServerUrlEdited)
        self.ui.pacsUrlLineEdit.connect("editingFinished()", self.onPacsUrlEdited)
        self.ui.checkConnectionButton.connect("clicked(bool)", self.onCheckConnection)

        # Stretch so the panel content stays at the top.
        self.layout.addStretch(1)

    def cleanup(self) -> None:
        pass

    def _showStatus(self, text: str, ok: bool) -> None:
        color = "#1a7f37" if ok else "#cf222e"
        self.ui.statusLabel.setStyleSheet(f"color: {color};")
        self.ui.statusLabel.text = text

    def onServerUrlEdited(self) -> bool:
        try:
            self.ui.serverUrlLineEdit.text = self.logic.setServerUrl(self.ui.serverUrlLineEdit.text)
        except monai_label.UrlError as error:
            self._showStatus(str(error), ok=False)
            return False
        return True

    def onPacsUrlEdited(self) -> bool:
        try:
            self.ui.pacsUrlLineEdit.text = self.logic.setPacsUrl(self.ui.pacsUrlLineEdit.text)
        except monai_label.UrlError as error:
            self._showStatus(str(error), ok=False)
            return False
        return True

    def onCheckConnection(self) -> None:
        self.ui.infoTextEdit.plainText = ""
        if not self.onServerUrlEdited():
            return
        self._showStatus(_("Connecting to {url} ...").format(url=self.logic.serverUrl()), ok=True)
        self.ui.checkConnectionButton.enabled = False
        slicer.app.processEvents()
        try:
            # Synchronous call with a short timeout: the UI is blocked at most
            # ICHTriageLogic.CONNECTION_TIMEOUT_SECONDS.
            with slicer.util.WaitCursor():
                info = self.logic.checkConnection()
        except monai_label.MonaiLabelError as error:
            self._showStatus(_("Connection failed: {error}").format(error=error), ok=False)
        else:
            self._showStatus(_("Connected to MONAI Label."), ok=True)
            self.ui.infoTextEdit.plainText = monai_label.format_info(info)
        finally:
            self.ui.checkConnectionButton.enabled = True


#
# ICHTriageLogic
#


class ICHTriageLogic(ScriptedLoadableModuleLogic):
    """Settings and server calls, usable without the widget.

    Settings are application-wide (QSettings), not part of the MRML scene, so
    this module has no parameter node.
    """

    SERVER_URL_SETTING = "ICHTriage/MonaiLabelServerUrl"
    PACS_URL_SETTING = "ICHTriage/PacsDicomWebUrl"
    CONNECTION_TIMEOUT_SECONDS = monai_label.DEFAULT_TIMEOUT_SECONDS

    def __init__(self) -> None:
        ScriptedLoadableModuleLogic.__init__(self)

    @staticmethod
    def _setting(key: str, default: str) -> str:
        value = qt.QSettings().value(key)
        return str(value) if value not in (None, "") else default

    def serverUrl(self) -> str:
        return self._setting(self.SERVER_URL_SETTING, monai_label.DEFAULT_SERVER_URL)

    def setServerUrl(self, url: str) -> str:
        """Validate, store and return the normalized MONAI Label server URL."""
        normalized = monai_label.normalize_server_url(url)
        qt.QSettings().setValue(self.SERVER_URL_SETTING, normalized)
        return normalized

    def pacsUrl(self) -> str:
        return self._setting(self.PACS_URL_SETTING, "")

    def setPacsUrl(self, url: str) -> str:
        """Validate, store and return the PACS DICOMweb root URL (may be empty)."""
        normalized = monai_label.normalize_dicomweb_url(url)
        qt.QSettings().setValue(self.PACS_URL_SETTING, normalized)
        return normalized

    def checkConnection(self, serverUrl: str | None = None) -> monai_label.AppInfo:
        """Call GET /info/ on the MONAI Label server. Raises monai_label.MonaiLabelError."""
        return monai_label.fetch_info(serverUrl or self.serverUrl(), timeout=self.CONNECTION_TIMEOUT_SECONDS)


#
# ICHTriageTest
#

# Minimal /info/ payload with the keys of MONAILabelApp.info() in MONAI Label 0.8.6.
_SAMPLE_INFO = {
    "name": "MONAILabel - Radiology (0.8.6)",
    "description": "DeepLearning models for radiology",
    "version": "0.8.6",
    "labels": ["spleen"],
    "models": {
        "segmentation_spleen": {
            "type": "segmentation",
            "labels": {"spleen": 1},
            "dimension": 3,
            "description": "A pre-trained model for volumetric (3D) segmentation of the spleen from CT image",
            "config": {"device": ["cpu"]},
        }
    },
    "trainers": {},
    "strategies": {"random": {"description": "Random Strategy"}},
    "scoring": {},
    "train_stats": {},
    "datastore": {"total": 3, "completed": 0, "label_tags": {}},
}


class _FakeMonaiLabelHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == monai_label.INFO_PATH:
            body = json.dumps(_SAMPLE_INFO).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass


def _unusedLocalPort() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class ICHTriageTest(ScriptedLoadableModuleTest):
    """Self-test, runs in the GUI (Reload and Test) or headless (--testing --no-main-window).

    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        slicer.mrmlScene.Clear()
        settings = qt.QSettings()
        self._savedSettings = {
            key: settings.value(key)
            for key in (ICHTriageLogic.SERVER_URL_SETTING, ICHTriageLogic.PACS_URL_SETTING)
        }

    def tearDown(self):
        settings = qt.QSettings()
        for key, value in self._savedSettings.items():
            if value is None:
                settings.remove(key)
            else:
                settings.setValue(key, value)

    def runTest(self):
        for test in (
            self.test_ModuleRegisteredInIchCategory,
            self.test_SettingsRoundTrip,
            self.test_CheckConnectionSuccess,
            self.test_CheckConnectionRefused,
            self.test_WidgetShowsConnectionError,
        ):
            self.setUp()
            try:
                test()
            finally:
                self.tearDown()
        self.delayDisplay("All ICHTriage tests passed")

    def test_ModuleRegisteredInIchCategory(self):
        self.delayDisplay("Module is registered in category ICH")
        module = slicer.modules.ichtriage
        self.assertEqual(module.title, "ICH Triage")
        self.assertIn("ICH", list(module.categories))

    def test_SettingsRoundTrip(self):
        self.delayDisplay("Settings round trip")
        logic = ICHTriageLogic()
        qt.QSettings().remove(ICHTriageLogic.SERVER_URL_SETTING)
        qt.QSettings().remove(ICHTriageLogic.PACS_URL_SETTING)
        self.assertEqual(logic.serverUrl(), "http://localhost:8000")
        self.assertEqual(logic.pacsUrl(), "")

        self.assertEqual(logic.setServerUrl(" http://wsl-host:8000/ "), "http://wsl-host:8000")
        self.assertEqual(logic.serverUrl(), "http://wsl-host:8000")
        with self.assertRaises(monai_label.UrlError):
            logic.setServerUrl("localhost:8000")
        self.assertEqual(logic.serverUrl(), "http://wsl-host:8000")

        url = "http://pacs:8080/dcm4chee-arc/aets/DCM4CHEE/rs"
        self.assertEqual(logic.setPacsUrl(url + "/"), url)
        self.assertEqual(logic.pacsUrl(), url)
        self.assertEqual(logic.setPacsUrl(""), "")
        self.assertEqual(logic.pacsUrl(), "")

    def test_CheckConnectionSuccess(self):
        self.delayDisplay("Check connection against a local fake MONAI Label server")
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _FakeMonaiLabelHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_address[1]}"
            info = ICHTriageLogic().checkConnection(url)
        finally:
            server.shutdown()
            server.server_close()
        self.assertEqual(info.name, "MONAILabel - Radiology (0.8.6)")
        self.assertEqual([model.name for model in info.models], ["segmentation_spleen"])
        self.assertEqual(info.trainers, ())

    def test_CheckConnectionRefused(self):
        self.delayDisplay("Check connection with no server reports an error without hanging")
        url = f"http://127.0.0.1:{_unusedLocalPort()}"
        start = time.monotonic()
        with self.assertRaises(monai_label.MonaiLabelConnectionError):
            ICHTriageLogic().checkConnection(url)
        self.assertLess(time.monotonic() - start, ICHTriageLogic.CONNECTION_TIMEOUT_SECONDS + 2)

    def test_WidgetShowsConnectionError(self):
        self.delayDisplay("Check connection button shows an error when no server runs")
        widget = slicer.modules.ichtriage.widgetRepresentation().self()
        widget.ui.serverUrlLineEdit.text = f"http://127.0.0.1:{_unusedLocalPort()}"
        widget.ui.checkConnectionButton.click()
        self.assertTrue(widget.ui.statusLabel.text.startswith("Connection failed:"), widget.ui.statusLabel.text)
        self.assertIn("connection refused", widget.ui.statusLabel.text)
        self.assertTrue(widget.ui.checkConnectionButton.enabled)
