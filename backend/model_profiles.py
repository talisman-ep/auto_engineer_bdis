from dataclasses import dataclass


@dataclass(frozen=True)
class ModelProfile:
    brand: str
    name: str
    body: str
    fuel: str
    drive: str
    first_year: int
    last_year: int
    min_hp: int
    max_hp: int
    min_acc: float
    max_acc: float
    turbo: bool


# Selected plausible synthetic configurations, not a manufacturer specification database.
# Each row covers a selected year window, not the full production history.
_BRANDS = '''Toyota|Японія|1937|масовий
Honda|Японія|1948|масовий
Mazda|Японія|1920|масовий
Nissan|Японія|1933|масовий
Subaru|Японія|1953|масовий
Hyundai|Південна Корея|1967|масовий
Kia|Південна Корея|1944|масовий
Ford|США|1903|масовий
Chevrolet|США|1911|масовий
Volkswagen|Німеччина|1937|масовий
Skoda|Чехія|1895|масовий
Renault|Франція|1899|масовий
Peugeot|Франція|1810|масовий
Fiat|Італія|1899|масовий
BMW|Німеччина|1916|преміум
Mercedes-Benz|Німеччина|1926|преміум
Audi|Німеччина|1909|преміум
Volvo|Швеція|1927|преміум
Lexus|Японія|1989|преміум
Jaguar|Велика Британія|1922|преміум
Porsche|Німеччина|1931|спорткари
Ferrari|Італія|1947|спорткари
Lamborghini|Італія|1963|спорткари
McLaren|Велика Британія|1963|гіперкари
Koenigsegg|Швеція|1994|гіперкари
Tesla|США|2003|преміум
Mitsubishi|Японія|1970|масовий
Suzuki|Японія|1909|масовий
Dacia|Румунія|1966|масовий
SEAT|Іспанія|1950|масовий
Cupra|Іспанія|2018|преміум
Opel|Німеччина|1862|масовий
Citroen|Франція|1919|масовий
Alfa Romeo|Італія|1910|преміум
Jeep|США|1941|масовий
Land Rover|Велика Британія|1948|преміум
Aston Martin|Велика Британія|1913|спорткари
Bentley|Велика Британія|1919|преміум
Bugatti|Франція|1909|гіперкари
BYD|Китай|2003|масовий
Polestar|Швеція|2017|преміум
Rimac|Хорватія|2009|гіперкари'''
BRANDS = [(name, country, int(year), segment) for name, country, year, segment in
          (line.split('|') for line in _BRANDS.splitlines())]

BODY_TYPES = ["Седан", "Купе", "Кросовер", "Хетчбек", "Універсал", "Родстер"]
FUEL_TYPES = ["Бензин", "Дизель", "Гібрид", "Електро"]
_BODIES = dict(zip('SCXHWR', BODY_TYPES))
_FUELS = dict(zip('PDHE', FUEL_TYPES))
_DRIVES = {'F': 'Передній', 'R': 'Задній', 'A': 'Повний'}

# brand | model/variant | body fuel drive | years | hp | 0-100 s | turbo (0/1)
_ROWS = '''Toyota|Corolla E100 1.6|SPF|1995|1997|105|115|10.0|12.5|0
Toyota|Corolla 1.6|SPF|2014|2018|120|132|10.0|12.0|0
Toyota|Corolla Hybrid|SHF|2019|2025|120|196|7.5|11.2|0
Toyota|Prius Hybrid|HHF|2023|2026|194|196|7.0|8.0|0
Toyota|RAV4 Hybrid|XHA|2019|2025|215|225|7.8|8.6|0
Toyota|GR Yaris|HPA|2021|2025|257|280|5.0|5.6|1
Toyota|bZ4X AWD|XEA|2022|2025|215|220|6.8|7.2|0
Toyota|Avensis 2.0 D-4D|WDF|2009|2015|124|150|9.5|11.0|1
Honda|Civic EK 1.4|HPF|1996|2000|90|90|11.0|13.0|0
Honda|Civic 1.5 Turbo|HPF|2017|2021|174|182|7.8|8.8|1
Honda|Civic e:HEV|HHF|2022|2025|180|184|7.7|8.3|0
Honda|CR-V Hybrid|XHA|2020|2025|184|204|8.0|9.5|0
Honda|Accord 2.0|SPF|2008|2015|150|156|9.5|11.0|0
Mazda|MX-5|RPR|2016|2024|131|184|6.5|8.5|0
Mazda|Mazda3 Skyactiv-G|HPF|2019|2024|120|165|8.0|11.0|0
Mazda|CX-5 Skyactiv-D AWD|XDA|2017|2023|150|184|9.0|11.0|1
Mazda|MX-30|XEF|2020|2023|143|145|9.5|10.0|0
Nissan|Qashqai dCi|XDF|2014|2019|110|130|9.8|12.5|1
Nissan|Leaf|HEF|2018|2023|147|214|6.9|8.2|0
Nissan|Ariya AWD|XEA|2022|2025|280|306|5.5|6.0|0
Nissan|GT-R|CPA|2009|2024|480|600|2.7|3.8|1
Subaru|Impreza 2.0|HPA|2017|2023|150|156|9.0|10.5|0
Subaru|WRX STI|SPA|2015|2020|300|310|4.9|5.5|1
Subaru|Forester e-BOXER|XHA|2019|2024|145|150|11.0|12.0|0
Hyundai|i30 1.4 T-GDI|HPF|2017|2020|138|140|8.5|9.5|1
Hyundai|Tucson CRDi|XDA|2016|2020|136|185|9.0|11.5|1
Hyundai|IONIQ 5 AWD|XEA|2022|2025|300|325|5.0|5.5|0
Hyundai|IONIQ 6 RWD|SER|2023|2025|225|229|7.0|7.6|0
Hyundai|Kona Hybrid|XHF|2020|2025|139|141|10.5|12.0|0
Kia|Ceed 1.6 CRDi|HDF|2013|2018|110|136|9.8|12.0|1
Kia|Sportage Hybrid|XHA|2022|2025|226|230|7.8|8.8|1
Kia|EV6 AWD|XEA|2022|2025|320|325|4.9|5.3|0
Kia|Niro Hybrid|XHF|2017|2025|139|141|10.5|12.0|0
Ford|Focus EcoBoost|HPF|2013|2018|100|150|8.8|12.5|1
Ford|Mondeo TDCi|WDF|2015|2019|150|180|8.5|10.5|1
Ford|Mustang GT|CPR|2018|2023|445|480|4.0|4.8|0
Ford|Mustang Mach-E AWD|XEA|2021|2025|260|346|4.8|6.0|0
Chevrolet|Malibu 1.5 Turbo|SPF|2016|2024|160|165|8.8|9.5|1
Chevrolet|Corvette Stingray C8|CPR|2020|2025|490|495|2.9|3.4|0
Chevrolet|Bolt EV|HEF|2017|2023|200|204|6.5|7.5|0
Volkswagen|Golf IV 1.9 TDI|HDF|1998|2003|90|130|9.6|13.0|1
Volkswagen|Golf GTI|HPF|2014|2024|210|245|6.2|7.0|1
Volkswagen|Passat 2.0 TDI|WDF|2015|2023|150|200|7.8|9.5|1
Volkswagen|ID.3 Pro|HER|2020|2025|145|204|7.2|9.6|0
Volkswagen|ID.4 GTX|XEA|2021|2025|299|340|5.3|6.3|0
Skoda|Octavia 2.0 TDI|WDF|2014|2023|150|200|7.5|9.3|1
Skoda|Fabia 1.0 TSI|HPF|2018|2025|95|115|9.5|11.5|1
Skoda|Enyaq iV 80|XER|2021|2024|201|204|8.0|8.9|0
Renault|Megane dCi|HDF|2016|2020|110|130|9.5|12.0|1
Renault|Clio E-Tech|HHF|2020|2025|140|145|9.3|10.3|0
Renault|Zoe|HEF|2019|2023|108|135|9.5|12.0|0
Peugeot|308 BlueHDi|HDF|2015|2023|120|130|9.5|11.0|1
Peugeot|3008 PureTech|XPF|2017|2022|130|180|8.0|10.5|1
Peugeot|e-208|HEF|2020|2025|136|156|8.0|9.2|0
Fiat|Tipo 1.6 MultiJet|SDF|2016|2020|120|130|9.5|10.5|1
Fiat|500e|HEF|2021|2025|95|118|9.0|10.0|0
BMW|328i E36|SPR|1995|1998|190|193|7.0|8.0|0
BMW|330i|SPR|2019|2025|245|258|5.7|6.3|1
BMW|320d|SDR|2019|2025|184|190|6.8|7.4|1
BMW|M3 Competition xDrive|SPA|2022|2025|503|530|3.4|3.8|1
BMW|X5 xDrive45e|XHA|2020|2023|389|394|5.3|5.8|1
BMW|i4 M50|HEA|2022|2025|536|544|3.8|4.0|0
BMW|iX xDrive50|XEA|2022|2025|516|523|4.4|4.9|0
Mercedes-Benz|C 200|SPR|2015|2018|184|184|7.2|7.8|1
Mercedes-Benz|E 220 d|SDR|2017|2023|194|200|7.0|7.8|1
Mercedes-Benz|GLC 300 e 4MATIC|XHA|2020|2025|315|333|6.0|6.7|1
Mercedes-Benz|AMG GT|CPR|2016|2021|462|585|3.5|4.0|1
Mercedes-Benz|EQS 450+|SER|2022|2025|329|360|5.8|6.5|0
Audi|A4 2.0 TDI|SDF|2016|2023|150|190|7.5|9.2|1
Audi|RS 6 Avant|WPA|2020|2025|591|630|3.3|3.7|1
Audi|Q5 TFSI e quattro|XHA|2020|2025|295|367|5.0|6.3|1
Audi|e-tron GT quattro|SEA|2022|2024|469|530|4.0|4.5|0
Volvo|V60 D4|WDF|2015|2020|181|190|7.5|8.5|1
Volvo|XC60 T8 AWD|XHA|2020|2025|390|455|4.8|5.5|1
Volvo|EX30 Twin Motor|XEA|2024|2025|422|428|3.6|3.8|0
Lexus|IS 300h|SHR|2014|2020|220|223|8.0|8.6|0
Lexus|RX 450h AWD|XHA|2016|2022|308|313|7.5|8.0|0
Lexus|RZ 450e|XEA|2023|2025|308|313|5.2|5.6|0
Jaguar|F-Type R AWD|CPA|2016|2024|550|575|3.5|4.2|0
Jaguar|I-PACE|XEA|2019|2024|394|400|4.6|4.9|0
Porsche|911 Carrera S|CPR|2020|2024|443|450|3.4|4.0|1
Porsche|911 GT3|CPR|2022|2025|502|510|3.2|3.9|0
Porsche|718 Boxster S|RPR|2017|2024|345|350|4.0|4.7|1
Porsche|Cayenne E-Hybrid|XHA|2019|2025|455|470|4.7|5.3|1
Porsche|Taycan 4S|SEA|2021|2024|520|571|3.8|4.2|0
Ferrari|488 GTB|CPR|2016|2019|661|670|2.9|3.2|1
Ferrari|F8 Tributo|CPR|2020|2022|710|720|2.8|3.1|1
Ferrari|SF90 Stradale|CHA|2020|2024|986|1000|2.4|2.7|1
Ferrari|296 GTB|CHR|2022|2025|819|830|2.8|3.1|1
Lamborghini|Huracan EVO AWD|CPA|2020|2023|630|640|2.8|3.1|0
Lamborghini|Urus|XPA|2019|2023|641|650|3.4|3.8|1
Lamborghini|Revuelto|CHA|2024|2025|1000|1015|2.4|2.7|0
McLaren|720S|CPR|2018|2022|710|720|2.8|3.1|1
McLaren|Artura|CHR|2023|2025|671|700|2.9|3.2|1
Koenigsegg|Agera RS|CPR|2016|2018|1160|1360|2.7|3.1|1
Koenigsegg|Jesko Attack|CPR|2023|2025|1280|1280|2.5|3.1|1
Koenigsegg|Jesko Absolut|CPR|2023|2025|1280|1280|2.5|3.1|1
Tesla|Model 3 RWD|SER|2019|2026|250|290|5.8|6.5|0
Tesla|Model 3 Performance|SEA|2021|2025|450|510|3.0|3.5|0
Tesla|Model Y Long Range AWD|XEA|2021|2025|350|390|4.8|5.3|0
Tesla|Model S Plaid|SEA|2022|2025|1000|1020|2.1|2.5|0
Mitsubishi|Outlander PHEV|XHA|2014|2024|200|248|8.0|11.0|0
Mitsubishi|Lancer Evolution X|SPA|2008|2015|291|300|4.7|5.5|1
Suzuki|Swift Sport|HPF|2018|2020|138|140|8.0|8.5|1
Suzuki|Vitara 1.6 DDiS|XDF|2015|2018|120|120|10.5|12.5|1
Dacia|Duster 1.5 dCi 4x4|XDA|2014|2023|110|115|11.0|13.0|1
Dacia|Spring|HEF|2021|2025|44|65|13.7|19.1|0
SEAT|Leon 2.0 TDI|HDF|2014|2023|150|184|7.5|9.0|1
SEAT|Ibiza 1.0 TSI|HPF|2018|2025|95|115|9.5|11.0|1
Cupra|Formentor VZ 2.0 TSI|XPA|2021|2025|300|333|4.8|5.1|1
Cupra|Born|HER|2022|2025|204|231|6.5|7.4|0
Opel|Astra 1.6 CDTI|HDF|2016|2019|110|136|9.5|11.5|1
Opel|Corsa Electric|HEF|2020|2025|136|156|8.1|9.2|0
Citroen|C4 BlueHDi|XDF|2021|2024|110|130|9.5|11.0|1
Citroen|e-C4|XEF|2021|2025|136|156|9.0|10.0|0
Alfa Romeo|Giulia Quadrifoglio|SPR|2017|2024|505|520|3.8|4.0|1
Alfa Romeo|Stelvio 2.2 Diesel Q4|XDA|2018|2024|190|210|6.6|7.5|1
Jeep|Wrangler 2.2 MultiJet|XDA|2019|2021|200|200|9.5|11.0|1
Jeep|Wrangler 4xe|XHA|2022|2025|375|380|6.0|6.8|1
Land Rover|Range Rover Sport D300|XDA|2021|2025|296|300|6.5|7.5|1
Land Rover|Range Rover Evoque D180|XDA|2019|2020|177|180|9.0|10.0|1
Aston Martin|Vantage V8|CPR|2019|2023|503|535|3.5|3.9|1
Aston Martin|DBX707|XPA|2023|2025|697|707|3.2|3.5|1
Bentley|Continental GT V8|CPA|2020|2023|542|550|3.8|4.2|1
Bentley|Bentayga Hybrid|XHA|2020|2024|443|462|5.3|5.8|1
Bugatti|Chiron|CPA|2017|2022|1479|1500|2.3|2.6|1
BYD|Dolphin|HEF|2023|2025|95|204|7.0|12.5|0
BYD|Seal AWD|SEA|2023|2025|523|530|3.7|3.9|0
BYD|Seal U DM-i AWD|XHA|2024|2025|319|324|5.8|6.3|1
Polestar|2 Long Range Dual Motor|HEA|2021|2025|402|476|4.0|4.8|0
Polestar|3 Long Range Dual Motor|XEA|2024|2025|483|517|4.5|5.1|0
Rimac|Nevera|CEA|2022|2025|1888|1914|1.8|2.1|0'''


def _parse(line: str) -> ModelProfile:
    brand, name, codes, y1, y2, hp1, hp2, a1, a2, turbo = line.split('|')
    return ModelProfile(brand, name, _BODIES[codes[0]], _FUELS[codes[1]],
                        _DRIVES[codes[2]], int(y1), int(y2), int(hp1), int(hp2),
                        float(a1), float(a2), turbo == '1')


MODEL_PROFILES = tuple(_parse(line) for line in _ROWS.splitlines())
