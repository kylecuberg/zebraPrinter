# Standard library
import os
import sys

# First-party/Local
import private
import util


class generalized_barcode_generation:
    def __init__(self, label_x=2, label_y=1, dpi=203, printer="zt411"):
        """create zebra printer string for the barcode labels.
        Run .wo_based, .excel_based, or .manual to generate the entry.
        Run .send to create the individual zebra strings & print
        """
        self.label_x = int(label_x)
        self.label_y = int(label_y)
        self.dpi = int(dpi)
        self.printer = str(printer)
        self.zitems = {}

    def excel_based(self, filename="Print_File.xlsb"):
        try:
            item_list = util.loop_xlsb_file(os.path.abspath(os.path.join(os.pardir(), "input", filename)), columns=1)
            if type(item_list) != list:
                item_list = [item_list]
            self.zitems = self.item_check(item_list)
        except Exception as E:
            print(E, type(E).__name__, __file__, E.__traceback__.tb_lineno)
        return item_list

    def manual(self, value=None):
        try:
            if value is None:
                item_list = [
                    "".join(str(input("Please type in Workorder, Barcode OR Cell_ID to print labels for: ")).strip())
                ]
            else:
                item_list = [value]
            self.zitems = self.item_check(item_list)
        except Exception as E:
            print(E, type(E).__name__, __file__, E.__traceback__.tb_lineno)
        return item_list

    def item_check(self, item_list):
        d = {}
        try:
            sparc = util.MySQL(
                os.getenv("mysql_user", private.mysql_user),
                os.getenv("mysql_password", private.mysql_password),
                os.getenv("mysql_host", private.mysql_host),
                database=os.getenv("mysql_database", "sparc"),
            )

            for item in item_list:
                cell_info_list = sparc.select(
                    rf"""select t.thingname, t.workorder, CASE WHEN g.thingname like 'CHG%%' THEN '' ELSE g.thingname END AS raw
                    from sparc.thing t
                    inner join sparc.genealogy g on g.parentthingname = t.thingname
                    where t.thingname like '{item}' or g.thingname like '{item}' or t.workorder like '{item}'
                    group by t.thingname, t.workorder, raw
                    order by t.thingname desc"""
                ).values.tolist()

                for cell_info in cell_info_list:
                    if cell_info[2] != "":
                        cell_info[2] = "Raw-" + cell_info[2]
                    d[cell_info[0]] = {"workorder": cell_info[1], "barcode": cell_info[2]}
        except Exception as E:
            print(E, type(E).__name__, __file__, E.__traceback__.tb_lineno)
        return d

    def zebra_text(self, **kwargs):
        dpi = kwargs.get("dpi", self.dpi)
        qr_loc = str(kwargs.get("qr_loc", str(round(0.080 * dpi, 0)) + "," + str(round(0.200 * dpi, 0))))
        cell_loc = str(kwargs.get("cell_loc", str(round(0.665 * dpi, 0)) + "," + str(round(0.246 * dpi, 0))))
        barcode_loc = str(kwargs.get("barcode_loc", str(round(0.665 * dpi, 0)) + "," + str(round(0.542 * dpi, 0))))
        workorder_loc = str(kwargs.get("workorder_loc", str(round(0.665 * dpi, 0)) + "," + str(round(0.739 * dpi, 0))))
        cell_text_size = str(
            kwargs.get("cell_text_size", str(round(0.200 * dpi, 0)) + "," + str(round(0.180 * dpi, 0)))
        )
        barcode_text_size = str(
            kwargs.get("barcode_text_size", str(round(0.100 * dpi, 0)) + "," + str(round(0.100 * dpi, 0)))
        )
        workorder_text_size = str(
            kwargs.get("workorder_text_size", str(round(0.200 * dpi, 0)) + "," + str(round(0.180 * dpi, 0)))
        )
        self.qr = f"""^XA
            ^FO{qr_loc},0^BQN,2,5,Q,7^FDQA,{kwargs.get("cell", "")}^FS
            ^CF0,{cell_text_size}^FO{cell_loc},0^FD{kwargs.get("cell", "")}^FS
            ^CF0,{barcode_text_size}^FO{barcode_loc},0^FD{kwargs.get("barcode", "")}^FS
            ^CF0,{workorder_text_size}^FO{workorder_loc},0^FD{kwargs.get("workorder", "")}^FS
            ^XZ"""
        return self.qr

    def send(self, **kwargs):
        for key, item in self.zitems.items():
            z = util.zebra(
                qr=self.zebra_text(
                    cell=key,
                    barcode=item.get("barcode", ""),
                    workorder=item.get("workorder", ""),
                    label_x=self.label_x,
                    label_y=self.label_y,
                    **kwargs,
                )
            )
            z.send(
                host=os.getenv(self.printer + "_host", private.zt411_host),
                port=os.getenv(self.printer + "_port", private.zt411_port),
            )

    def reset(self):
        self.zitems = {}
        self.item_list = []


def manual():
    gbg = generalized_barcode_generation()
    while True:
        gbg.manual()
        gbg.send()
        gbg.reset()


def excel():
    gbg = generalized_barcode_generation()
    gbg.excel_based()
    gbg.send()


if __name__ == "__main__":
    """[summary]"""
    try:
        globals()[sys.argv[1]]()
    except Exception as E:
        gbg = generalized_barcode_generation()
        gbg.manual("SLEV230324292")
        gbg.send()
        gbg.reset()
        print(E, type(E).__name__, __file__, E.__traceback__.tb_lineno)