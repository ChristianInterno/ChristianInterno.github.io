# -*- coding: utf-8 -*-
"""
Everything the site says lives in this file.

Edit it, then run   python3 build.py   to regenerate the pages.
Text fields may contain simple HTML such as <a href="...">links</a> or <i>italics</i>.
Authors: write full names; add a trailing * for equal contribution.
"""

SITE = {
    "name": "Christian Internò",
    "url": "https://christianinterno.com",
    # While this is False, every page asks search engines not to list it (people with the link can still visit).
    # Set it to True when the site is ready, rebuild, and push.
    "listed": False,
    "title": "Researcher, Bielefeld University",
    "interests": "World models, physical reasoning and distributed learning.",
    "tagline": "I study how neural networks model the physical world, and how they learn together.",
    "email": "christian.interno@uni-bielefeld.de",
    "links": [
        ("Email", "mailto:christian.interno@uni-bielefeld.de"),
        ("Scholar", "https://scholar.google.com/citations?user=melu9g0AAAAJ"),
        ("GitHub", "https://github.com/ChristianInterno"),
        ("Hugging Face", "https://huggingface.co/CInterno"),
        ("LinkedIn", "https://www.linkedin.com/in/christian-interno/"),
        ("X", "https://x.com/ChrisInterno"),
    ],
    "scholar": "https://scholar.google.com/citations?user=melu9g0AAAAJ",
    "dblp": "https://dblp.org/pid/358/4928.html",
    # Drop a PDF at assets/cv.pdf and a "CV" link appears in the menu automatically.
    "cv": "assets/cv.pdf",
}

BIO = [
    'I am a researcher at Bielefeld University, working with <a href="https://hammer-lab.techfak.uni-bielefeld.de/">Barbara Hammer</a>; '
    'my PhD is funded by the <a href="https://www.honda-ri.de/">Honda Research Institute Europe</a>. After a Visiting Fellowship in '
    'Philip Torr’s <a href="https://torrvision.com/">Torr Vision Group</a> at the <a href="https://www.ox.ac.uk/">University of Oxford</a>, '
    'I continue to work with the group on world models.',
    'My <a href="/publications/">research</a> focuses on world models and physical reasoning: I read the geometry of learned '
    'representations to find out what neural networks know about physics, and use it to tell whether a generated video could '
    'really happen. Broadly, I want physical plausibility to become something we can measure: principled ways to read physics '
    'out of a model, and to put that structure to work as a prior for learning, a verifier at inference time and a diagnostic '
    'for anomalies. Alongside this, I work on distributed learning, where many models learn together without sharing their data.',
    'I have been a visiting researcher at <a href="https://www.cshl.edu/">Cold Spring Harbor Laboratory</a> and Leiden University, '
    'and I studied data science at the University of Milano-Bicocca.',
]

# Newest first. The first `NEWS_SHOWN` items are visible; the rest fold under "Earlier news".
# Set "next": True for something that hasn't happened yet.
NEWS_SHOWN = 7
NEWS = [
    {"date": "Dec 2026", "next": True, "text": "<b>Next:</b> NeurIPS 2026 in Sydney."},
    {"date": "Oct 2026", "text": '<a href="https://arxiv.org/abs/2610.22655"><i>Is a Linear Probe Evidence of a Linear Representation?</i></a> is on arXiv.'},
    {"date": "Oct 2026", "text": 'Released the GeoPhys <a href="https://github.com/ChristianInterno/GeoPhys">code on GitHub</a> and the '
                                 '<a href="https://huggingface.co/datasets/CInterno/GeoPhys-features">feature dataset</a> on Hugging Face.'},
    {"date": "Sep 2026", "text": '<b>Two papers accepted at NeurIPS 2026:</b> <a href="https://arxiv.org/abs/2606.20707">GeoPhys</a>, and '
                                 '<a href="https://arxiv.org/abs/2610.22655"><i>Is a Linear Probe Evidence of a Linear Representation?</i></a> '
                                 'as joint first author.'},
    {"date": "Sep 2026", "text": 'Two new preprints: <a href="https://arxiv.org/abs/2609.37631">Procedural Core</a> and <a href="https://arxiv.org/abs/2609.23881">MotionJEPA</a>.'},
    {"date": "Jul 2026", "text": '<a href="https://doi.org/10.1109/JIOT.2026.3686028"><i>Pruning Federated Models Through Loss Landscape '
                                 'Analysis and Client Agreement Scoring</i></a> is out in the <b>IEEE Internet of Things Journal</b>.'},
    {"date": "Jun 2026", "text": '<b>GeoPhys reached first place</b> in video-to-video generation on both <a href="https://github.com/google-deepmind/physics-IQ-benchmark">Physics&#8209;IQ leaderboards</a>.'},
    {"date": "Jun 2026", "text": "Started a Visiting Fellowship in Philip Torr’s group at the University of Oxford."},
    {"date": "Jun 2026", "text": "<i>Geodesic-SVDD Latent Mixup for One-Shot Distributed Tabular Learning</i> at IJCNN 2026 in Maastricht."},
    {"date": "Feb 2026", "text": '<a href="https://arxiv.org/abs/2602.12218">The Observer Effect in World Models</a> is on arXiv.'},
    {"date": "Jan 2026", "text": "PPFLex at the AAAI 2026 workshop on federated learning for critical applications."},
    {"date": "Dec 2025", "text": 'At NeurIPS 2025 in San Diego with <a href="https://arxiv.org/abs/2507.00583">ReStraV</a>, and '
                                 '<a href="https://arxiv.org/abs/2509.17999">the Narcissus Hypothesis</a> at a workshop.'},
    {"date": "Dec 2024", "text": 'Oral at the <a href="https://neurips.cc/virtual/2024/workshop/84740">NeurIPS 2024 International Workshop '
                                 'on Federated Foundation Models</a>, on <a href="https://arxiv.org/abs/2405.10271">adaptive hybrid pruning '
                                 'in federated learning</a>.'},
]

# The two lines of work. Papers, research themes and the publications filter use these keys.
LINES = {"rep": "World models and physical reasoning", "dist": "Distributed learning"}

# kind: "pub" (published or accepted) or "pre" (preprint)
# line: "rep" (world models and physical reasoning), "dist" (distributed learning) or "other"
# bib: "conf" (booktitle), "journal" or "arxiv"
PAPERS = [
    {
        "key": "interno2026geophys", "short": "GeoPhys", "kind": "pub", "line": "rep", "year": 2026, "selected": True,
        "summary": "Five geometric measures of a video’s path through frozen image encoders tell physically plausible videos from implausible ones without any training, and, used as a verifier, pick the most plausible of a video generator’s candidates.",
        "title": "GeoPhys: The Geometry of Physical Plausibility",
        "authors": ["Christian Internò", "Alexander Pondaven", "Habon Issa", "Fabio Pizzati", "Francesco Pinto",
                    "Markus Olhofer", "Ivan Laptev", "Philip Torr", "Eero P. Simoncelli", "Barbara Hammer", "David Klindt"],
        "badge": "NeurIPS 2026", "venue": "", "bib": "conf", "booktitle": "Advances in Neural Information Processing Systems",
        "arxiv": "2606.20707",
        "links": [("arXiv", "https://arxiv.org/abs/2606.20707"), ("code", "https://github.com/ChristianInterno/GeoPhys"),
                  ("data", "https://huggingface.co/datasets/CInterno/GeoPhys-features"), ("project page", "/GeoPhys/")],
        "flags": ["First on both Physics&#8209;IQ video&#8209;to&#8209;video leaderboards"],
    },
    {
        "key": "kutluozen2026linear", "short": "Linear probe", "kind": "pub", "line": "rep", "year": 2026, "selected": True,
        "summary": "A linear probe that reads a property out of a network is often taken as proof that the network represents it linearly; we ask when that conclusion actually holds.",
        "title": "Is a Linear Probe Evidence of a Linear Representation?",
        "authors": ["Nadir Kutluozen*", "Christian Internò*", "David Klindt"],
        "badge": "NeurIPS 2026", "venue": "", "bib": "conf", "booktitle": "Advances in Neural Information Processing Systems",
        "arxiv": "2610.22655",
        "links": [("arXiv", "https://arxiv.org/abs/2610.22655")],
    },
    {
        "key": "interno2026pruning", "short": "AutoFLIP", "kind": "pub", "line": "dist", "year": 2026, "selected": True,
        "summary": "Clients explore the loss landscape together once before training, and that shared map guides how the federated model is pruned, cutting computation by about half and communication by about two thirds on non-IID data.",
        "title": "Pruning Federated Models Through Loss Landscape Analysis and Client Agreement Scoring",
        "authors": ["Christian Internò", "Elena Raponi", "Markus Olhofer", "Ali Raza", "Thomas Bäck", "Niki van Stein",
                    "Yaochu Jin", "Barbara Hammer"],
        "badge": "IoT-J 2026", "venue": "IEEE Internet of Things Journal", "bib": "journal",
        "journal": "IEEE Internet of Things Journal", "volume": "13", "number": "14", "pages": "31283--31293",
        "doi": "10.1109/JIOT.2026.3686028", "arxiv": "2405.10271",
        "links": [("journal", "https://doi.org/10.1109/JIOT.2026.3686028"), ("arXiv", "https://arxiv.org/abs/2405.10271"),
                  ("code", "https://github.com/ChristianInterno/AutoFLIP")],
        "flags": ["Oral at the NeurIPS 2024 workshop FL@FM"],
    },
    {
        "key": "yuca2026ppflex", "short": "PPFLex", "kind": "pub", "line": "dist", "year": 2026,
        "summary": "Secure multi-party computation for the optimisation of federated models on non-IID data, so that collaborating does not mean revealing what each client holds.",
        "title": "PPFLex: Securing Non-IID Optimization in Federated Learning via MPC",
        "authors": ["Nergiz Yuca", "Christian Internò", "Nikolay Matyunin", "Markus Olhofer", "Barbara Hammer", "Stefan Katzenbeisser"],
        "badge": "AAAI-W 2026", "venue": "AAAI 2026 Workshop on Federated Learning for Critical Applications", "bib": "conf",
        "booktitle": "AAAI 2026 Workshop on Federated Learning for Critical Applications",
        "links": [],
    },
    {
        "key": "interno2025restrav", "short": "ReStraV", "kind": "pub", "line": "rep", "year": 2025, "selected": True,
        "summary": "Real videos trace straighter paths than generated ones through the representations of a self-supervised vision model, and a small classifier on that curvature spots AI-generated video.",
        "title": "AI-Generated Video Detection via Perceptual Straightening",
        "authors": ["Christian Internò", "Robert Geirhos", "Markus Olhofer", "Sunny Liu", "Barbara Hammer", "David Klindt"],
        "badge": "NeurIPS 2025", "venue": "", "bib": "conf", "booktitle": "Advances in Neural Information Processing Systems",
        "arxiv": "2507.00583",
        "links": [("arXiv", "https://arxiv.org/abs/2507.00583"), ("code", "https://github.com/ChristianInterno/ReStraV")],
        "flags": ["Cited in a forensic report by Hany Farid"],
    },
    {
        "key": "cadei2025narcissus", "short": "Narcissus Hypothesis", "kind": "pub", "line": "other", "year": 2025,
        "summary": "Personality assessments and a new social-desirability score across 31 foundation models show them drifting toward agreeable, socially conforming answers.",
        "title": "The Narcissus Hypothesis: Descending to the Rung of Illusion",
        "authors": ["Riccardo Cadei*", "Christian Internò*"],
        "badge": "NeurIPS-W 2025", "venue": "NeurIPS 2025 Workshop on Evaluating the Evolving LLM Lifecycle", "bib": "conf",
        "booktitle": "NeurIPS 2025 Workshop on Evaluating the Evolving LLM Lifecycle", "arxiv": "2509.17999",
        "links": [("arXiv", "https://arxiv.org/abs/2509.17999")],
    },
    {
        "key": "interno2024fedlex", "short": "FedLEx", "kind": "pub", "line": "dist", "year": 2024, "selected": True,
        "summary": "Clients measure how their gradients deviate across parameters, and the steering matrix built from that short exploration guides federated training on non-IID data.",
        "title": "Federated Loss Exploration for Improved Convergence on Non-IID Data",
        "authors": ["Christian Internò", "Markus Olhofer", "Yaochu Jin", "Barbara Hammer"],
        "badge": "IJCNN 2024", "venue": "", "bib": "conf", "booktitle": "2024 International Joint Conference on Neural Networks (IJCNN)",
        "doi": "10.1109/IJCNN60899.2024.10651455", "arxiv": "2506.18640",
        "links": [("paper", "https://doi.org/10.1109/IJCNN60899.2024.10651455"), ("arXiv", "https://arxiv.org/abs/2506.18640"),
                  ("code", "https://github.com/ChristianInterno/FedLEx")],
    },
    {
        "key": "karmann2026motionjepa", "short": "MotionJEPA", "kind": "pre", "line": "rep", "year": 2026,
        "summary": "A regulariser that predicts embeddings of frame differences keeps JEPA world models from holding on to slow features only, giving fuller latents and better planning.",
        "title": "MotionJEPA: Preventing Temporal Feature Collapse by Capturing Visual Changes in Latent Space",
        "authors": ["Markus Karmann*", "Shile Li*", "Christian Internò", "Bruno Andreis", "David Klindt", "Randall Balestriero",
                    "Jindong Gu", "Philip Torr", "Qi Zhang", "Peng-Tao Jiang", "Hao Zhang", "Bo Li", "Onay Urfalioglu"],
        "badge": "arXiv 2026", "venue": "", "bib": "arxiv", "arxiv": "2609.23881",
        "links": [("arXiv", "https://arxiv.org/abs/2609.23881")],
    },
    {
        "key": "shinnick2026procedural", "short": "Procedural Core", "kind": "pre", "line": "rep", "year": 2026,
        "summary": "A small recurrent transformer pretrained on procedurally generated data is expanded to initialise vision transformers of any size, and lifts ViT-Base on ImageNet by 2.2 points.",
        "title": "Procedural Core: A Compact Recurrent Initialization for Vision Transformers",
        "authors": ["Zachary Shinnick", "Christian Internò", "Hemanth Saratchandran", "Anton van den Hengel", "Damien Teney"],
        "badge": "arXiv 2026", "venue": "", "bib": "arxiv", "arxiv": "2609.37631",
        "links": [("arXiv", "https://arxiv.org/abs/2609.37631")],
    },
    {
        "key": "interno2026observer", "short": "Observer Effect", "kind": "pre", "line": "rep", "year": 2026,
        "summary": "Adapting a world model to read out its physics can change the physics it represents; PhyIP reads it from frozen features instead, with a lightweight probe.",
        "title": "The Observer Effect in World Models: Invasive Adaptation Corrupts Latent Physics",
        "authors": ["Christian Internò", "Jumpei Yamaguchi", "Loren Amdahl-Culleton", "Markus Olhofer", "David Klindt", "Barbara Hammer"],
        "badge": "arXiv 2026", "venue": "", "bib": "arxiv", "arxiv": "2602.12218",
        "links": [("arXiv", "https://arxiv.org/abs/2602.12218")],
    },
    {
        "key": "moleri2026federatedfactory", "short": "FederatedFactory", "kind": "pre", "line": "dist", "year": 2026,
        "summary": "Each client sends a generative model instead of model weights, so a single round of communication is enough even when every client holds different classes.",
        "title": "FederatedFactory: Generative One-Shot Learning for Extremely Non-IID Distributed Scenarios",
        "authors": ["Andrea Moleri*", "Christian Internò*", "Ali Raza", "Markus Olhofer", "David Klindt", "Fabio Stella", "Barbara Hammer"],
        "badge": "arXiv 2026", "venue": "", "bib": "arxiv", "arxiv": "2603.16370",
        "links": [("arXiv", "https://arxiv.org/abs/2603.16370")],
    },
    {
        "key": "interno2025industrial", "short": "SIDED", "kind": "pre", "line": "other", "year": 2025,
        "summary": "A digital-twin dataset of industrial energy use, and a light augmentation method that helps models disaggregate complex equipment such as combined heat and power plants.",
        "title": "Industrial Energy Disaggregation with Digital Twin-generated Dataset and Efficient Data Augmentation",
        "authors": ["Christian Internò", "Andrea Castellani", "Sebastian Schmitt", "Fabio Stella", "Barbara Hammer"],
        "badge": "arXiv 2025", "venue": "", "bib": "arxiv", "arxiv": "2506.20525",
        "links": [("arXiv", "https://arxiv.org/abs/2506.20525"), ("dataset", "https://github.com/ChristianInterno/SIDED")],
    },
]

PATENTS = "Inventor on two European patent applications from my work at the Honda Research Institute."

THEMES = [
    {
        "id": "representations", "line": "rep",
        "title": "World models and physical reasoning",
        "figure": "bounce",
        "text": "Neural networks see the world through their representations. I ask what those representations encode about physics, "
                "and how to read it out without changing the model in the process.",
    },
    {
        "id": "distributed", "line": "dist",
        "title": "Distributed learning",
        "figure": "islands",
        "text": "Many models, many owners, and data that never leaves home. I work on how such models can still learn together "
                "when their data barely overlap, and how to keep that collaboration small, fast and private.",
    },
]

# glyph: bounce, straight, kinked, prune, landscape, signal, frames
CODE = [
    {"name": "GeoPhys", "venue": "NeurIPS 2026", "glyph": "bounce",
     "text": "Training-free physical plausibility from the trajectory geometry of frozen image encoders.",
     "links": [("GitHub", "https://github.com/ChristianInterno/GeoPhys"), ("project page", "/GeoPhys/")]},
    {"name": "GeoPhys features", "venue": "Hugging Face dataset", "glyph": "frames",
     "text": "Precomputed encoder features and the Physics&#8209;IQ candidate videos used in GeoPhys.",
     "links": [("Hugging Face", "https://huggingface.co/datasets/CInterno/GeoPhys-features")]},
    {"name": "ReStraV", "venue": "NeurIPS 2025", "glyph": "kinked",
     "text": "Detecting AI-generated video with perceptual straightening.",
     "links": [("GitHub", "https://github.com/ChristianInterno/ReStraV")]},
    {"name": "AutoFLIP", "venue": "IEEE Internet of Things Journal", "glyph": "prune",
     "text": "Automated federated learning via informed pruning.",
     "links": [("GitHub", "https://github.com/ChristianInterno/AutoFLIP")]},
    {"name": "FedLEx", "venue": "IJCNN 2024", "glyph": "landscape",
     "text": "Federated loss exploration for better convergence on non-IID data.",
     "links": [("GitHub", "https://github.com/ChristianInterno/FedLEx")]},
    {"name": "SIDED", "venue": "Dataset", "glyph": "signal",
     "text": "A digital-twin dataset for industrial energy disaggregation.",
     "links": [("GitHub", "https://github.com/ChristianInterno/SIDED")]},
]

# the Collaborate page: a short invitation, then co-authors (taken from PAPERS), students and service
COLLABORATE = [
    'Most of my work is done with others. If you work on world models, physical reasoning or distributed learning, '
    'or have a problem where they could help, write to me at '
    '<a href="mailto:christian.interno@uni-bielefeld.de">christian.interno@uni-bielefeld.de</a>.',
    'A few lines are enough to start: what you work on, and the question you have in mind.',
]

# posts themselves are Markdown files in posts/ (see build.py)
BLOG_INTRO = "Notes on research, and on the things I build along the way."

MENTORING = [
    {"date": "2025", "who": "Andrea Moleri", "where": "MSc student, University of Milano-Bicocca",
     "what": 'Master’s thesis at the Honda Research Institute, which became '
             '<a href="/publications/#moleri2026federatedfactory">FederatedFactory</a>.'},
    {"date": "2025", "who": "Jumpei Yamaguchi", "where": "MSc student, Tokyo Institute of Technology",
     "what": 'Research internship at the Honda Research Institute, which fed into '
             '<a href="/publications/#interno2026observer"><i>The Observer Effect in World Models</i></a>.'},
]

SERVICE = "Reviewer for NeurIPS, ICML, IJCNN and the World Modeling Workshop at Mila."

VOLUNTEERING = [
    {"date": "2024", "text": "Educational sports activities and teaching in Malawi, with Africathletics."},
    {"date": "2019", "text": "Teaching people with psycho-motor disabilities in Salvador de Bahia, Brazil, with the Sacramentine Sisters."},
    {"date": "2018", "text": "Educational sports activities and teaching in Malawi, with the Sacramentine Sisters."},
]

FOOTNOTE = ("I grew up on Lake Iseo, Italy. The walkway is for Christo and Jeanne-Claude’s "
            '<a href="https://en.wikipedia.org/wiki/The_Floating_Piers"><i>The Floating Piers</i></a>, '
            "which crossed the lake to Monte Isola in the summer of 2016. The water beside it follows "
            '<a href="/blog/the-lake/">linear wave theory for deep water</a>, '
            '<span class="nw"><i>ω</i>² = <i>gk</i> + (<i>σ</i>/<i>ρ</i>)<i>k</i>³</span>: the breeze’s long waves roll in slowly, '
            "and the short ripples from a touch run out ahead of them.")
