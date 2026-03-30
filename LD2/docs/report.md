# Elektroninės parduotuvės kūrimo ataskaita

## 1. Projekto tikslas

Šio darbo tikslas buvo sukurti atvirojo kodo elektroninę parduotuvę, pritaikytą mažam arba vidutiniam verslui. Projekto koncepcijai pasirinkta **rankų darbo papuošalų parduotuvė**, nes ši niša leidžia aiškiai pateikti katalogą, sukurti estetišką dizainą ir patogiai įgyvendinti kategorijų bei atsiliepimų funkcijas.

Parduotuvė turėjo atitikti šiuos pagrindinius reikalavimus:
- turėti bent 20 produktų;
- produktai turėjo būti suskirstyti bent į 3 kategorijas;
- kiekvienas produktas turėjo turėti pavadinimą, aprašymą, kainą ir bent vieną nuotrauką;
- turėjo būti įdiegta klientų atsiliepimų apie prekes funkcija;
- turėjo būti parengta aiški ir struktūruota ataskaita.

## 2. Pasirinktos technologijos

Projektui pasirinkta **PrestaShop** platforma, nes ji yra atvirojo kodo, tinkama smulkiam ir vidutiniam verslui, turi patogų administravimo skydelį, leidžia importuoti produktus iš CSV failų, palaiko temų naudojimą ir papildomų modulių diegimą.

Naudotos technologijos:
- **PrestaShop 9** - elektroninės parduotuvės platforma;
- **MariaDB 11** - duomenų bazė;
- **Docker Compose** - virtualizuota paleidimo aplinka;
- **Nginx** - statiniams produktų paveikslėliams pateikti importo metu;
- **CSV duomenų failai** - produktų ir kategorijų importui;
- **Product Comments** modulis - klientų atsiliepimams ir įvertinimams.

## 3. Duomenų paruošimas

Produktų katalogas buvo parengtas demonstracinių duomenų principu. Kaip pagrindas pasirinktas PrestaShop ekosistemos metodas, kai pradinis katalogas sugeneruojamas arba sudaromas automatiškai, o vėliau pritaikomas konkrečiai verslo sričiai. Vietoje atsitiktinio katalogo buvo suformuotas vientisas rankų darbo papuošalų asortimentas.

Sukurta 20 produktų ir 4 kategorijos:
- Necklaces;
- Bracelets;
- Earrings;
- Rings.

Kiekvienam produktui buvo paruošta:
- pavadinimas;
- trumpas ir pilnas aprašymas;
- kaina;
- kategorija;
- bent viena iliustracija.

Duomenys saugomi šiuose failuose:
- `data/categories.csv`;
- `data/products.csv`;
- `data/products.import.csv`.

Produktų importui sukurtas papildomas scenarijus `scripts/prepare_import.py`, kuris santykinius paveikslėlių kelius paverčia absoliučiais URL adresais. Tai palengvina PrestaShop importą, nes produktų nuotraukos gali būti pasiekiamos per lokalų statinį serverį.

## 4. Produktų katalogo struktūra

Katalogo struktūra parinkta taip, kad vartotojui būtų paprasta naršyti prekes ir lyginti panašius gaminius. Kategorijos atitinka papuošalų tipus, todėl lankytojas gali greitai pereiti prie jį dominančių produktų.

### 4.1. Produktų sąrašas

| Kategorija | Produktų skaičius | Pavyzdiniai produktai |
|---|---:|---|
| Necklaces | 5 | Amber Drop Necklace, Rose Quartz Pendant |
| Bracelets | 5 | Baltic Amber Bracelet, Adjustable Boho Bracelet |
| Earrings | 5 | Moonlight Earrings, Floral Clay Earrings |
| Rings | 5 | Silver Wave Ring, Black Stone Ring |

Bendrai kataloge pateikta 20 produktų.

## 5. Platformos diegimas ir konfigūracija

Projektas buvo pritaikytas paleidimui naudojant `Docker Compose`, todėl sistema gali būti lengvai pakartojama kitame kompiuteryje arba virtualioje aplinkoje.

Pagrindiniai paleidžiami servisai:
- `prestashop` - pagrindinė parduotuvės aplikacija;
- `db` - MariaDB duomenų bazė;
- `images` - statinis serveris produktų paveikslėliams.

Failas `docker-compose.yml` nustato:
- duomenų bazės prisijungimo parametrus;
- automatinį PrestaShop diegimą;
- administratoriaus prisijungimo duomenis;
- prievadus `8080` ir `8081`;
- duomenų saugojimo tomus.

Tokia konfigūracija leidžia greitai paleisti parduotuvę komanda:

```bash
docker compose up -d
```

## 6. Dizainas ir navigacija

Parduotuvės dizaino kryptis pasirinkta atsižvelgiant į rankų darbo papuošalų temą. Pagrindiniai sprendimai:
- šviesus fonas;
- švelnios auksinės, rausvos ir žemiškos spalvos;
- didelės produktų iliustracijos;
- aiškus kategorijų išdėstymas;
- vizualiai tvarkingos produktų kortelės.

Navigacija numatyta taip, kad naudotojas galėtų lengvai pereiti tarp:
- pradžios puslapio;
- produktų kategorijų;
- atskiro produkto puslapio;
- atsiliepimų skilties.

Tokio tipo dizainas tinka smulkaus verslo elektroninei parduotuvei, nes išlaiko balansą tarp estetikos ir funkcionalumo.

## 7. Atsiliepimų funkcijos įgyvendinimas

Klientų atsiliepimų funkcijai pasirinktas **Product Comments** modulis. Jis leidžia:
- vartotojams palikti žvaigždučių įvertinimą;
- parašyti tekstinį komentarą;
- rodyti atsiliepimus produkto puslapyje;
- taikyti moderavimą prieš publikuojant atsiliepimą.

Ši funkcija tiesiogiai atitinka užduoties reikalavimą sudaryti galimybę vartotojams rašyti atsiliepimus apie prekes. Be to, atsiliepimai didina pasitikėjimą parduotuve ir padeda būsimam pirkėjui įvertinti produktą.

## 8. Testavimas ir optimizavimas

Buvo atliktas pagrindinių funkcijų testavimas:
- parduotuvės paleidimas;
- kategorijų atvaizdavimas;
- produktų importas;
- produktų puslapių atvaizdavimas;
- nuotraukų rodymas;
- atsiliepimų formos veikimas;
- prisitaikymas prie mažesnių ekranų.

### 8.1. Testavimo rezultatai

| Testas | Laukiamas rezultatas | Faktinis rezultatas | Būsena |
|---|---|---|---|
| Pagrindinis puslapis atsidaro | Svetainė pasiekiama be klaidų | Veikia korektiškai | Atlikta |
| Kategorijos rodomos | Matomas produktų sąrašas | Veikia korektiškai | Atlikta |
| Produktai importuojami | Importuojami visi 20 produktų | Veikia korektiškai | Atlikta |
| Nuotraukos įkeliamos | Visi produktai turi iliustracijas | Veikia korektiškai | Atlikta |
| Atsiliepimo forma veikia | Vartotojas gali palikti komentarą | Veikia korektiškai | Atlikta |
| Mobilus vaizdas tvarkingas | Turinys prisitaiko prie ekrano | Veikia korektiškai | Atlikta |

### 8.2. Aptiktos problemos ir sprendimai

1. **Nuotraukų importavimo problema** - santykiniai paveikslėlių keliai nebuvo patikimi, todėl pridėtas atskiras Nginx statinis serveris ir scenarijus importo CSV failui sugeneruoti.
2. **Katalogo vientisumas** - automatiškai sugeneruoti duomenys dažnai atrodo per daug bendriniai, todėl produktų pavadinimai, aprašymai ir kainos buvo rankiniu būdu suvienodinti.
3. **Atsiliepimų kontrolė** - siekiant tvarkingo testavimo, rekomenduota įjungti moderavimo funkciją.

## 9. Inovatyvūs sprendimai

Siekiant geresnio įvertinimo ir didesnio vartotojo patogumo, siūlomi šie papildomi sprendimai:
- pagrindiniame puslapyje rodyti „Featured products“ bloką;
- sukurti „New arrivals“ sekciją;
- aktyvuoti paiešką ir filtravimą pagal kategoriją arba kainą;
- naudoti SEO draugiškus URL;
- pateikti susijusius produktus produkto puslapyje.

Šie sprendimai gerina naudotojo patirtį ir padeda parduotuvei atrodyti profesionalesnei.

## 10. Išvada

Sukurtas elektroninės parduotuvės projektas atitinka užduoties reikalavimus. Parengtas ne mažesnis kaip 20 produktų katalogas, produktai suskirstyti į 4 kategorijas, kiekvienas produktas turi pavadinimą, aprašymą, kainą ir nuotrauką. Platformai pasirinkta atvirojo kodo PrestaShop sistema, paleidžiama virtualizuotoje Docker aplinkoje. Taip pat įgyvendinta klientų atsiliepimų funkcija naudojant Product Comments modulį.

Galutinis sprendimas yra pakankamai pilnas, kad galėtų būti pademonstruotas kaip veikiantis akademinis projektas, o papildomai siūlomos funkcijos sudaro pagrindą tolimesniam tobulinimui.
