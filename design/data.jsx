// Conversation history + message data — realistic SAPA / bureau d'études context

const HISTORY = [
  { id: "c1", title: "Adaptation mur-rideau Elegance 52",   meta: "Aujourd'hui · 14:32", group: "today",     active: true },
  { id: "c2", title: "Profilés porteurs SAPA 70 GTI+",       meta: "Aujourd'hui · 11:08", group: "today" },
  { id: "c3", title: "Joints EPDM coupe AA",                  meta: "Hier · 17:21",        group: "yesterday" },
  { id: "c4", title: "Vérification SP24808 vs SP24803",      meta: "Hier · 09:45",        group: "yesterday" },
  { id: "c5", title: "Compatibilité Performance 70 / 90",    meta: "26 avr. · 16:02",     group: "week" },
  { id: "c6", title: "Coupe horizontale traverse basse",     meta: "26 avr. · 10:14",     group: "week" },
  { id: "c7", title: "Nomenclature porte EI30",               meta: "24 avr.",             group: "week" },
  { id: "c8", title: "Seuil PMR — référence SA48994",         meta: "22 avr.",             group: "older" },
  { id: "c9", title: "Calcul Uw double vitrage 28mm",         meta: "20 avr.",             group: "older" },
];

const HISTORY_GROUPS = [
  { key: "today",     label: "Aujourd'hui" },
  { key: "yesterday", label: "Hier" },
  { key: "week",      label: "7 derniers jours" },
  { key: "older",     label: "Plus ancien" },
];

const PROFILES = [
  { ref: "SGC0332",  desc: "Parclose" },
  { ref: "SJ27847",  desc: "Profilé latéral" },
  { ref: "SP24808",  desc: "Profilé central" },
  { ref: "SJ28377",  desc: "Profilé central" },
  { ref: "SP24803",  desc: "Profilé d'assemblage" },
  { ref: "SRU0034",  desc: "Profilé intermédiaire" },
  { ref: "SP26164",  desc: "Adaptateur" },
  { ref: "SBT6001",  desc: "Profilé de liaison" },
  { ref: "S210055",  desc: "Profilé inférieur" },
  { ref: "S93084",   desc: "Profilé inférieur" },
  { ref: "SA54894",  desc: "Seuil / base" },
];

const SOURCES = [
  { doc: "Catalogue SAPA Performance 70",    section: "COUPES — Adaptation mur-rideau Elegance 52", page: 217 },
  { doc: "Catalogue SAPA Performance 70",    section: "Nomenclature profilés section C",            page: 218 },
  { doc: "Fiche technique Elegance 52",      section: "Compatibilités",                              page: 12  },
];

const SUGGESTIONS = [
  { ic: "🔧", txt: "Donne-moi la coupe AA de cette adaptation" },
  { ic: "📐", txt: "Quelles sont les dimensions du SP24808 ?" },
  { ic: "🧱", txt: "Profilés équivalents en gamme Performance 90" },
  { ic: "🔗", txt: "Compatibilité avec mur-rideau Elegance 72" },
];

const STARTERS = [
  { lbl: "Nomenclature",  q: "Liste des profilés porteurs pour la SAPA 70 GTI+ en applique" },
  { lbl: "Compatibilité", q: "La gamme Performance 70 est-elle compatible avec Elegance 72 ?" },
  { lbl: "Dimensions",    q: "Section et inertie du profilé SP24808" },
  { lbl: "Joints",        q: "Quel joint EPDM utiliser pour la coupe BB de l'adaptation Elegance 52 ?" },
];

window.HISTORY = HISTORY;
window.HISTORY_GROUPS = HISTORY_GROUPS;
window.PROFILES = PROFILES;
window.SOURCES = SOURCES;
window.SUGGESTIONS = SUGGESTIONS;
window.STARTERS = STARTERS;
