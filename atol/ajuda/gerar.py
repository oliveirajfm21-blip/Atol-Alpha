"""
Gerador das imagens de ajuda
============================

Desenha as fórmulas (matplotlib mathtext) e as figuras dos cartões de ajuda,
no estilo SciencePlots, e salva em atol/ajuda/imagens.

Uso (na pasta do Atol):
    python -m atol.ajuda.gerar
"""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from skimage import data, restoration, filters
import os
from pathlib import Path
OUT = str(Path(__file__).resolve().parent / "imagens")
import scienceplots  # noqa: F401
plt.style.use(["science", "no-latex"])          # padrão de artigo pedido pelo professor
# cores do ciclo do SciencePlots: preto para o principal, azul/vermelho para comparar
OC, LA, CO, SU, BG, LI = "#000000", "#0C5DA5", "#FF2C00", "#474747", "#FFFFFF", "#D3E0DE"
plt.rcParams.update({"mathtext.fontset": "cm", "font.size": 11})

FORMULAS = {
 "escala_pitagoras": r"d_{px} = \sqrt{(x_2-x_1)^2 + (y_2-y_1)^2}",
 "escala_s": r"s = \dfrac{d_{px}}{d_{real}}",
 "escala_conv": r"L_{real} = \dfrac{L_{px}}{s} \qquad A_{real} = \dfrac{A_{px}}{s^2}",
 "escala_erro": r"\dfrac{\Delta s}{s} \approx \dfrac{1}{z \, d_{px}}",
 "fundo_sub": r"I_{corr}(x,y) = I(x,y) - F(x,y)",
 "fundo_abertura": r"F = (I \ominus b_r) \oplus b_r",
 "fundo_raio": r"r_{maior\ objeto} \;<\; r \;<\; r_{varia\c{c}\~ao\ do\ fundo}",
 "mediana": r"I'(x,y) = \mathrm{mediana}\{\, I(u,v) : (u,v) \in W_r(x,y) \,\}",
 "mediana_raio": r"r_{ru\acute{\imath}do} \;<\; r \;<\; r_{menor\ objeto}",
 "ws_dist": r"D(p) = \min_{q \,\in\, \mathrm{fundo}} \Vert p - q \Vert",
 "ws_h": r"\mathrm{pico\ aceito} \Leftrightarrow D_{pico} - D_{sela} \geq h",
 "tabela_sturges": r"k = \lceil \log_2 n \rceil + 1",
 "tabela_fracao": r"f_A = \dfrac{A_{objetos}}{A_{total}} \times 100\%",
 "grao_l": r"\bar{\ell} = \dfrac{L}{P}",
 "grao_G": r"G = -6{,}6439\,\log_{10}\bar{\ell} - 3{,}288",
 "grao_aniso": r"A_I = \dfrac{\bar{\ell}_{horizontal}}{\bar{\ell}_{vertical}}",
 "medir_d": r"d = \dfrac{\sqrt{(x_2-x_1)^2 + (y_2-y_1)^2}}{s}",
 "medir_ang": r"\theta = \mathrm{atan2}(-\Delta y,\ \Delta x)",
 "hv": r"HV = \dfrac{2F\sin(136^\circ/2)}{d^2} \approx 1{,}8544\,\dfrac{F}{d^2}",
 "hv_erro": r"\dfrac{\Delta HV}{HV} \approx 2\,\dfrac{\Delta d}{d}",
 "contraste": r"I'(x,y) = \min\left(255,\ \max\left(0,\ f \cdot I(x,y)\right)\right)",
 "limiar_b": r"B(x,y) = 1 \ \mathrm{se}\ I(x,y) > T, \ \mathrm{sen\~ao}\ 0",
 "limiar_iso": r"T_{k+1} = \dfrac{\mu_{fundo}(T_k) + \mu_{objeto}(T_k)}{2}",
 "limiar_otsu": r"T^* = \arg\max_T \ \omega_0(T)\,\omega_1(T)\,\left[\mu_0(T) - \mu_1(T)\right]^2",
 "diametro": r"d = 2\sqrt{\dfrac{A}{\pi}}",
 "tabela_circ": r"C = \dfrac{4\pi A}{P^2}",
 "tabela_desvio": r"\sigma = \sqrt{\dfrac{1}{n-1}\sum_{i=1}^{n}\left(d_i - \bar{d}\right)^2}",
 "tabela_escada": r"\dfrac{P_{escada}}{P_{real}} \approx \dfrac{4}{\pi} \approx 1{,}27",
}

def formula(nome, tex):
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, f"${tex}$", fontsize=15, color=OC)
    fig.savefig(f"{OUT}/f_{nome}.png", dpi=130, transparent=True, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)

def eixo(ax):
    """Quem manda no visual é o estilo SciencePlots; aqui só ajusta o tamanho dos números."""
    ax.tick_params(labelsize=8)
    from matplotlib.ticker import FuncFormatter
    virgula = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))   # 12,5 em vez de 12.5
    ax.xaxis.set_major_formatter(virgula); ax.yaxis.set_major_formatter(virgula)

def fig_fundo():
    x = np.arange(0, 401); I = 200 - 0.35 * x
    for a, b in [(40, 80), (200, 240), (310, 350)]:
        I += 100 / (1 + np.exp(-(x - a) * 1.2)) - 100 / (1 + np.exp(-(x - b) * 1.2))
    fig, axs = plt.subplots(2, 2, figsize=(6.4, 3.9), dpi=110, sharex=True)
    fig.patch.set_facecolor(BG)
    for c, (r, cor, nome) in enumerate([(10, LA, "raio 10: pequena demais"), (50, CO, "raio 50: maior que os objetos")]):
        F = restoration.rolling_ball(I, radius=r)
        a, b = axs[0, c], axs[1, c]
        a.plot(x, I, color=OC, lw=1.4); a.plot(x, F, color=cor, lw=2)
        a.set_title(f"Bola de {nome}", loc="left", color=OC, fontsize=9, fontweight="bold")
        a.set_ylim(0, 300)
        b.plot(x, I - F, color=cor, lw=1.8); b.set_ylim(-10, 130)
        b.set_title("Resultado  I − F", loc="left", color=SU, fontsize=8)
        eixo(a); eixo(b)
    fig.tight_layout(); fig.savefig(f"{OUT}/g_fundo.png", facecolor=BG); plt.close(fig)

def fig_contraste():
    I = np.linspace(0, 255, 256)
    fig, ax = plt.subplots(figsize=(4.6, 2.9), dpi=110); fig.patch.set_facecolor(BG)
    for f, cor, est in [(0.5, SU, "--"), (1.0, OC, "-"), (2.0, CO, "-")]:
        ax.plot(I, np.clip(f * I, 0, 255), color=cor, lw=2, ls=est, label=f"f = {f:.1f}".replace(".", ","))
    ax.annotate("satura em 255", (128, 255), xytext=(150, 200), color=CO, fontsize=8,
                arrowprops=dict(arrowstyle="-", color=CO, lw=.8))
    ax.set_xlabel("brilho de entrada I", color=SU, fontsize=8); ax.set_ylabel("brilho de saída I'", color=SU, fontsize=8)
    ax.set_xlim(0, 255); ax.set_ylim(0, 270); ax.legend(frameon=False, fontsize=8, labelcolor=OC, loc="lower right")
    eixo(ax); fig.tight_layout(); fig.savefig(f"{OUT}/g_contraste.png", facecolor=BG); plt.close(fig)

def fig_limiar():
    img = data.coins()
    t_iso, t_otsu = filters.threshold_isodata(img), filters.threshold_otsu(img)
    fig, ax = plt.subplots(figsize=(4.8, 2.8), dpi=110); fig.patch.set_facecolor(BG)
    h, _ = np.histogram(img, bins=256, range=(0, 256))
    ax.fill_between(np.arange(256), h, color="#9DB6BA", step="mid", lw=0)
    ax.axvline(t_iso, color=CO, lw=2); ax.axvline(t_otsu, color=LA, lw=2, ls="--")
    ymax = h.max()
    ax.text(t_iso + 3, ymax * .9, f"IsoData T = {t_iso:.0f}", color="#C2364A", fontsize=8)
    ax.text(t_otsu + 3, ymax * .75, f"Otsu T = {t_otsu:.0f}", color="#137A71", fontsize=8)
    ax.text(30, ymax * .55, "fundo", color=SU, fontsize=8); ax.text(170, ymax * .25, "moedas", color=SU, fontsize=8)
    ax.set_xlabel("brilho (0–255)", color=SU, fontsize=8); ax.set_ylabel("nº de pixels", color=SU, fontsize=8)
    ax.set_xlim(0, 255); eixo(ax); fig.tight_layout(); fig.savefig(f"{OUT}/g_limiar.png", facecolor=BG); plt.close(fig)

def fig_mediana():
    from scipy import ndimage as ndi
    x = np.arange(20); I = np.where(x < 10, 40.0, 200.0); I[5] = 255; I[14] = 60
    fig, ax = plt.subplots(figsize=(4.8, 2.8), dpi=110); fig.patch.set_facecolor(BG)
    ax.plot(x, I, color=SU, lw=1.2, marker="o", ms=3, label="original (com ruído)")
    ax.plot(x, ndi.uniform_filter1d(I, 5, mode="nearest"), color=CO, lw=2, label="média (janela 5)")
    ax.plot(x, ndi.median_filter(I, 5, mode="nearest"), color=LA, lw=2.2, ls="--", label="mediana (janela 5)")
    ax.set_xlabel("posição do pixel", color=SU, fontsize=8); ax.set_ylabel("brilho", color=SU, fontsize=8)
    ax.set_ylim(0, 340); ax.legend(frameon=False, fontsize=8, labelcolor=OC, loc="upper left", ncol=2)
    eixo(ax); fig.tight_layout(); fig.savefig(f"{OUT}/g_mediana.png", facecolor=BG); plt.close(fig)

def fig_watershed():
    x = np.linspace(0, 60, 400)
    D = np.maximum(0, np.maximum(16 - abs(x - 18), 16 - abs(x - 42)))
    D = np.minimum(D, np.where(abs(x - 30) < 30, 99, 0))
    fig, ax = plt.subplots(figsize=(4.8, 2.6), dpi=110); fig.patch.set_facecolor(BG)
    ax.fill_between(x, D, color=LA, alpha=.25, lw=0); ax.plot(x, D, color=OC, lw=2)
    ax.axvline(30, color=CO, lw=2, ls="--")
    ax.text(31, 14, "linha de corte\n(sela)", color="#C2364A", fontsize=8)
    ax.text(15, 16.8, "centro 1", color=OC, fontsize=8); ax.text(39, 16.8, "centro 2", color=OC, fontsize=8)
    ax.set_xlabel("posição ao longo das duas moedas", color=SU, fontsize=8); ax.set_ylabel("D (px)", color=SU, fontsize=8)
    ax.set_ylim(0, 20); eixo(ax); fig.tight_layout(); fig.savefig(f"{OUT}/g_watershed.png", facecolor=BG); plt.close(fig)

def fig_grao():
    from skimage import segmentation
    from atol.nucleo import medir_intercepto
    rng = np.random.default_rng(3)
    h, w = 180, 300
    pts = rng.random((40, 2)) * [h, w]
    yy, xx = np.mgrid[0:h, 0:w]
    d = ((yy[..., None] - pts[:, 0]) ** 2 + (xx[..., None] - pts[:, 1]) ** 2)
    lab = d.argmin(axis=2) + 1
    grao = ~segmentation.find_boundaries(lab, mode="inner")
    r = medir_intercepto(grao, 4)
    fig, ax = plt.subplots(figsize=(4.8, 2.9), dpi=110); fig.patch.set_facecolor(BG)
    ax.imshow(grao, cmap="gray", vmin=0, vmax=1)
    for x1, y1, x2, y2 in r["linhas"]:
        ax.plot([x1 - .5, x2 - .5], [y1 - .5, y2 - .5], color=LA, lw=1.4)
    xs, ys = zip(*r["pontos"]); ax.scatter(np.array(xs) - .5, np.array(ys) - .5, s=14, color=CO, zorder=3, edgecolors="white", linewidths=.6)
    ax.axis("off"); fig.tight_layout(); fig.savefig(f"{OUT}/g_grao.png", facecolor=BG); plt.close(fig)

def fig_contar():
    fig, axs = plt.subplots(1, 2, figsize=(4.6, 2.3), dpi=110); fig.patch.set_facecolor(BG)
    for ax, (titulo, viz) in zip(axs, [("Vizinhança-4", [(0, 1), (1, 0), (2, 1), (1, 2)]),
                                       ("Vizinhança-8 (usada no Atol)", [(i, j) for i in range(3) for j in range(3) if (i, j) != (1, 1)])]):
        for i in range(3):
            for j in range(3):
                cor = OC if (i, j) == (1, 1) else (LA if (i, j) in viz else "#EFF5F4")
                ax.add_patch(plt.Rectangle((j, 2 - i), .92, .92, color=cor))
        ax.set_xlim(-.1, 3); ax.set_ylim(-.1, 3); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(titulo, color=OC, fontsize=9, fontweight="bold")
    fig.tight_layout(); fig.savefig(f"{OUT}/g_contar.png", facecolor=BG); plt.close(fig)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for n, t in FORMULAS.items(): formula(n, t)
    fig_fundo(); fig_mediana(); fig_watershed(); fig_grao(); fig_contraste(); fig_limiar(); fig_contar()
    print(sorted(os.listdir(OUT)))
