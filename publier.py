# Publie une voiture addon de MWCoop (demande de JD, 21/10 : les voitures a part, telechargees et mises a jour par le
# lanceur, onglet Addons). Depuis ce dossier :
#   python -I publier.py <dossier de l'addon, ex. ...\extension\MWCoop\addons\t16> <version> [--modmin 1.7.2] [--sec]
# Fait : paquet <cle>-<version>.zip (<cle>\..., Version= ajoute a addon.ini, LISEZMOI public), apercus\<cle>.png,
# section [<cle>] de catalogue.txt, release <cle>-<version> sur GitHub (jamais remplacee : une nouvelle version = une
# nouvelle release), commit et push du catalogue. --sec : prepare seulement (rien sur GitHub).
# Retrait d'une voiture (un createur la reconnait) : python -I publier.py --retirer <cle> (section enlevee du catalogue ;
# les lanceurs ne la proposent plus), puis supprimer ses releases a la main.
import os, re, shutil, subprocess, sys, tempfile, zipfile

DEPOT = "Parricidium/MWCoop-Addons"
ICI = os.path.dirname(os.path.abspath(__file__))
CAT = os.path.join(ICI, "catalogue.txt")

LISEZMOI = """{nom} {ver} -- voiture addon de MWCoop (My Winter Car co-op)

FR
Installation : lanceur MWCoop, Addons, bouton Telecharger (les mises a jour arrivent au meme endroit).
A la main : copier le dossier {cle} dans <jeu>\\MWCoop\\addons.
En jeu : F10, onglet Voitures, bouton {court}. Les joueurs qui ne l'ont pas voient une VAZ-2108.
Modele 3D, textures et sons : mod rFactor 1 "Rally Cars" (RC), tout le merite revient a leurs auteurs d'origine ;
marques et logos retires, conversion pour MWCoop par Parricidium. Auteur d'origine et tu veux qu'elle soit retiree :
ouvre une issue sur https://github.com/{depot} (ou dis-le sur le Discord de MWCoop), elle le sera.

EN
Install: MWCoop launcher, Add-ons, Download button (updates come the same way).
By hand: copy the {cle} folder into <game>\\MWCoop\\addons.
In game: F10, Cars tab, {court} button. Players without it see a VAZ-2108.
3D model, textures and sounds: rFactor 1 "Rally Cars" (RC) mod, all credit to their original authors; brands and
logos removed, converted for MWCoop by Parricidium. Original author and you want it removed: open an issue on
https://github.com/{depot} (or say so on the MWCoop Discord) and it will be.
"""


def lire_ini(chemin):
    d = {}
    for l in open(chemin, encoding="utf-8-sig").read().splitlines():
        if "=" in l and not l.startswith((";", "[")):
            k, v = l.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def lire_catalogue():
    sections, cle = {}, None
    if os.path.exists(CAT):
        for l in open(CAT, encoding="utf-8-sig").read().splitlines():
            m = re.match(r"^\[([A-Za-z0-9_-]+)\]$", l)
            if m:
                cle = m.group(1); sections[cle] = []
            elif cle and l.strip():
                sections[cle].append(l)
    return sections


def ecrire_catalogue(sections):
    t = ["; Catalogue des voitures addons de MWCoop, lu par le lanceur (onglet Addons). Genere par publier.py.", ""]
    for cle in sorted(sections):
        t.append("[" + cle + "]"); t += sections[cle]; t.append("")
    open(CAT, "w", encoding="utf-8", newline="\n").write("\n".join(t))


def git(*a):
    subprocess.run(["git", "-c", "user.name=JD", "-c", "user.email=andarelli.jdo@gmail.com"] + list(a), cwd=ICI, check=True)


def retirer(cle):
    s = lire_catalogue()
    if cle not in s:
        sys.exit("pas au catalogue : " + cle)
    del s[cle]
    ecrire_catalogue(s)
    git("add", "-A")
    git("commit", "-q", "-m", "Retrait de " + cle + " du catalogue\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
    git("push", "-q", "origin", "main")
    print("retire du catalogue :", cle)


def main():
    a = sys.argv[1:]
    if a[:1] == ["--retirer"]:
        return retirer(a[1])
    sec = "--sec" in a
    modmin = a[a.index("--modmin") + 1] if "--modmin" in a else "1.7.2"
    src, ver = os.path.abspath(a[0]), a[1]
    cle = os.path.basename(src.rstrip("\\/"))
    ini = lire_ini(os.path.join(src, "addon.ini"))
    nom, court = ini.get("Nom", cle), ini.get("NomCourt", ini.get("Nom", cle))
    if not os.path.exists(os.path.join(src, "carrosserie.p205")):
        sys.exit("pas d'addon ici : " + src)
    os.makedirs(os.path.join(ICI, "sortie"), exist_ok=True)
    paquet = os.path.join(ICI, "sortie", f"{cle}-{ver}.zip")
    with tempfile.TemporaryDirectory() as tmp:
        st = os.path.join(tmp, cle)
        shutil.copytree(src, st)
        # (infos.txt GARDE : positions des roues, du volant, des charnieres et des feux, lues par le mod -- l'avoir retire
        # dans les premiers paquets du 21/10 donnait des roues du jeu trop hautes et un apercu sans roues, retour de JD)
        if not os.path.exists(os.path.join(st, "infos.txt")):
            sys.exit("infos.txt manquant dans " + src + " : le mod ne placerait pas les roues")
        lignes = [l for l in open(os.path.join(st, "addon.ini"), encoding="utf-8-sig").read().splitlines() if not l.startswith("Version=")]
        lignes.insert(1 if lignes and lignes[0].startswith("[") else 0, "Version=" + ver)
        open(os.path.join(st, "addon.ini"), "w", encoding="utf-8", newline="\r\n").write("\n".join(lignes) + "\n")
        open(os.path.join(st, "LISEZMOI.txt"), "w", encoding="utf-8", newline="\r\n").write(LISEZMOI.format(nom=nom, ver=ver, cle=cle, court=court, depot=DEPOT))
        with zipfile.ZipFile(paquet, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for r, _, fs in os.walk(st):
                for f in sorted(fs):
                    p = os.path.join(r, f)
                    z.write(p, os.path.relpath(p, tmp).replace("\\", "/"))
    shutil.copyfile(os.path.join(src, "apercu.png"), os.path.join(ICI, "apercus", cle + ".png"))
    taille = os.path.getsize(paquet)
    url = f"https://github.com/{DEPOT}/releases/download/{cle}-{ver}/{cle}-{ver}.zip"
    s = lire_catalogue()
    s[cle] = [f"Version={ver}", f"Nom={nom}", f"NomCourt={court}", f"Description={ini.get('Description', '')}",
              f"DescriptionEn={ini.get('DescriptionEn', '')}", f"Livree={ini.get('Livree', '0')}", f"Taille={taille}",
              f"Paquet={url}", f"Apercu=https://raw.githubusercontent.com/{DEPOT}/main/apercus/{cle}.png", f"ModMin={modmin}"]
    ecrire_catalogue(s)
    print(f"{cle} {ver} : {paquet} ({taille} octets)")
    if sec:
        return
    notes = f"{nom} {ver} -- MWCoop add-on car. Install it from the MWCoop launcher (Add-ons tab)."
    subprocess.run(["gh", "release", "create", f"{cle}-{ver}", paquet, "--repo", DEPOT, "--title", f"{nom} {ver}", "--notes", notes], cwd=ICI, check=True)
    git("add", "-A", "catalogue.txt", "apercus")
    git("commit", "-q", "-m", f"{nom} {ver}\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
    git("push", "-q", "origin", "main")
    print("publie :", url)


if __name__ == "__main__":
    main()
