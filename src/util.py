# Standard library
import csv
import os
import socket

# Third-party
import pandas as pd
from pyxlsb import open_workbook
from sqlalchemy import create_engine

# First-party/Local
import private


class zebra:
    def __init__(self, qr, conn_type="ip"):
        self.qr = qr
        self.conn_type = conn_type

    def _check_host_port(self, host, port):
        if host == "":
            host = os.getenv("ops_host", private.zt411_host)
        if port == "":
            port = int(os.getenv("ops_port", private.zt411_port))
        return host, port

    def create_ip_conn(self, **kwargs):
        host = kwargs.get("host", "")
        port = kwargs.get("port", "")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            host, port = self._check_host_port(host, port)
            sock.connect((host, int(port)))
        except Exception as E:
            print(type(E).__name__, __file__, E.__traceback__.tb_lineno, "\n", E)
        return sock

    def create_blue_conn(self, **kwargs):
        host = kwargs.get("host", "")
        port = kwargs.get("port", "")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            host, port = self._check_host_port(host, port)
            sock.connect((host, int(port)))
        except Exception as E:
            print(type(E).__name__, __file__, E.__traceback__.tb_lineno, "\n", E)
        return sock

    def send(self, **kwargs):
        if self.conn_type == "ip":
            self.sock = self.create_ip_conn(host=kwargs.get("host", ""), port=kwargs.get("port", ""))
        elif self.conn_type == "bluetooth":
            self.sock = self.create_blue_conn(host=kwargs.get("host", ""), port=kwargs.get("port", ""))
        self.sock.send(bytes(self.qr, "utf-8"))  # using bytes
        self.sock.close()


def loop_csv_file(filename):
    lines = []
    with open(filename) as read_obj:
        for row in csv.reader(read_obj):
            lines.append(row)
    return lines


def loop_xlsb_file(filename="input/Print_File.xlsb", sheetname="PRINT", columns=1):
    li = []
    with open_workbook(filename) as wb:
        with wb.get_sheet(sheetname) as sheet:
            try:
                for row in sheet.rows():
                    val = [r.v for r in row]
                    if val[0] is not None:
                        li.append(val[0:columns])  # retrieving content
            except Exception as E:
                print(E, type(E).__name__, __file__, E.__traceback__.tb_lineno)
    return li[1:]


class MySQL:
    def __init__(
        self,
        user,
        password,
        host,
        **kwargs,
    ):
        self.database = kwargs.get("database", "sparc")

        try:
            self.engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}/{self.database}")
        except Exception as E:
            print(E, type(E).__name__, __file__, E.__traceback__.tb_lineno)

    def select(self, query_text):
        """Get info from MySQL with select statement

        Args:
            query_text (string): Query to run

        Returns:
            Dataframe: Query results
        """
        try:
            df = pd.read_sql_query(query_text, con=self.engine)
        except Exception as E:
            print(E, type(E).__name__, __file__, E.__traceback__.tb_lineno)
            df = None
        return df


class qr_text:
    def __init__(self, **kwargs):
        self.dpi = kwargs.get("dpi", 203)
        self.label_x = kwargs.get("x", 2)
        self.label_y = kwargs.get("y", 1)
        self.qr = ""

    def sn(self, cell, barcode):
        qr_loc = str(round(0.075 * self.dpi, 0)) + "," + str(round(0.2 * self.dpi, 0))
        cell_loc = str(round(0.665 * self.dpi, 0)) + "," + str(round(0.45 * self.dpi, 0))
        barcode_loc = str(round(0.665 * self.dpi, 0)) + "," + str(round(0.8 * self.dpi, 0))
        cell_text_size = str(round(0.2 * self.dpi, 0)) + "," + str(round(0.16 * self.dpi, 0))
        barcode_text_size = str(round(0.1 * self.dpi, 0)) + "," + str(round(0.1 * self.dpi, 0))
        self.qr = f"""^XA
            ^FO{qr_loc},0^BQN,2,5,Q,7^FDQA,{cell}^FS
            ^CF0,{cell_text_size}^FO{cell_loc},0^FD{cell}^FS
            ^CF0,{barcode_text_size}^FO{barcode_loc},0^FDRaw-{barcode}^FS
            ^XZ"""
        return self.qr

    def boxlabel(self, lot, batch, cellformat, celllocation):
        text_size = str(round(self.dpi * 0.3), 0) + "," + str(round(self.dpi * 0.256, 0))
        self.qr = f"""^XA
                    ^CF0,{text_size}^FO20,20,0^FDLot:^FS
                    ^CF0,{text_size}^FO20,120,0^FDBatch:^FS
                    ^CF0,{text_size}^FO20,220,0^FDFormat:^FS
                    ^CF0,{text_size}^FO20,320,0^FDLocation:^FS
                    ^GB{str(self.label_x * self.dpi)},0,1,B,1^FO0,{str(0.5 * self.dpi)},0^FS
                    ^GB{str(self.label_x * self.dpi)},0,1,B,1^FO0,{str(1 * self.dpi)},0^FS
                    ^GB{str(self.label_x * self.dpi)},0,1,B,1^FO0,{str(1.5 * self.dpi)},0^FS
                    ^CF0,{text_size}^FO550,20,1^FD{lot}^FS
                    ^CF0,{text_size}^FO550,120,1^FD{batch}^FS
                    ^CF0,{text_size}^FO550,220,1^FD{cellformat}^FS
                    ^CF0,{text_size}^FO550,320,1^FD{celllocation}^FS
                    ^XZ"""
        return self.qr

    def process_boxlabel(self, lot, batch, cellformat, celllocation, qty):
        text_size = str(round(self.dpi * 0.3), 0) + "," + str(round(self.dpi * 0.256, 0))
        self.qr = f"""^XA
                    ^CF0,{text_size}^FO20,20,0^FDLot:^FS
                    ^CF0,{text_size}^FO20,100,0^FDBatch:^FS
                    ^CF0,{text_size}^FO20,180,0^FDFormat:^FS
                    ^CF0,{text_size}^FO20,260,0^FDLocation:^FS
                    ^CF0,{text_size}^FO20,340,0^FDQty:^FS
                    ^GB{str(self.label_x * self.dpi)},0,1,B,1^FO0,{str(0.4 * self.dpi)},0^FS
                    ^GB{str(self.label_x * self.dpi)},0,1,B,1^FO0,{str(0.8 * self.dpi)},0^FS
                    ^GB{str(self.label_x * self.dpi)},0,1,B,1^FO0,{str(1.2 * self.dpi)},0^FS
                    ^GB{str(self.label_x * self.dpi)},0,1,B,1^FO0,{str(1.6 * self.dpi)},0^FS
                    ^CF0,{text_size}^FO550,20,1^FD{lot}^FS
                    ^CF0,{text_size}^FO550,100,1^FD{batch}^FS
                    ^CF0,{text_size}^FO550,180,1^FD{cellformat}^FS
                    ^CF0,{text_size}^FO550,240,1^FD{celllocation}^FS
                    ^CF0,{text_size}^FO550,340,1^FD{qty}^FS
                    ^XZ"""
        return self.qr
