from Rdconverter import converter
import os


def test_convert():
    path, name = os.path.split(__file__)
    rd_path = os.path.join(path, 'test-data', 'test.Rd')
    data = converter(rd_path, 'Seurat')
    len(data)