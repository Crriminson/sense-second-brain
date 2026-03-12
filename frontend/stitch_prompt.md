**Project Overview**
Concept: A local-first, AI-powered second brain web application that provides the fastest path from raw thought to structured knowledge. The application lets users voice-capture ideas, process them, and view their expanded notes.
Core Features & Requirements:
- A Home page matching the exact specific content, text, and layout structure of the "ThoughtCapture v2" screenshot provided.
- The Dashboard view (header and stats ribbon primarily) must perfectly match the dark theme and deep navy aesthetic of the adniaconseils.ca hero section (green dots, black/navy background).
- Fluid scroll animations integrated throughout the page.
- Each captured note should feature a noticeable, smooth hover and reveal transition, making the cards feel interactive and premium.
- A functional "process idea" state/interaction. After processing, all resulting notes entirely remain expanded by default (no accordions) so complex ideas are easily readable without extra clicks.
- A rough draft of the code required to build the scroll animations must be provided.

**Visual Language**
Overall Aesthetic Mood: Corporate Tech-Minimalist. Sophisticated, high-tech, data-driven, clean but highly premium.
Color Palette:
- Backgrounds: Deep navy/midnight blue (`#000824` to `#00103A`) continuously across all pages (Home, Capture, and Dashboard). Feature the subtle green particle or "data-mist" effect across the background.
- Accents: Vibrant mint/neon green (`#00F291`) used for primary buttons, highlights, badges, and status indicators.
- Text: High-contrast white (`#FFFFFF`) on dark backgrounds.
Typography Style:
- Heading Font: Neue Montreal (or a similar geometric sans-serif). Bold weight, tight letter-spacing (-0.02em), highly professional appearance.
- Body Font: Roboto or Poppins (sans-serif). Regular weight, high legibility, generous line-height (1.5).
Spacing and Layout Patterns:
- Generous white space with massive vertical padding between prominent sections (120px+).
- Centered alignment for main text blocks with wide gutters.
- 2 or 3-column responsive grid structures for content cards.
- Occasional asymmetrical alignments (e.g., offset icons next to aligned text).
Animation and Interaction Feel:
- Momentum-based smooth scroll (fluid, friction-based feeling).
- Elements fade in and slide up (reveal) uniformly as they enter the viewport.
- Interactive subtle green particle or parallax effects on the dark background.
- Specific transitions on each captured note component: soft hover lifts, border glow, and smooth reveals upon scroll.
- Count-up animations for any numeric metric displays. 

**Page-by-Page UI Plan**
1. Home Page:
   - Header: Minimalist transparent to opaque navbar. Left side contains the logo text "ThoughtCapture" (White) and a small badge "v2 - Second Brain". Right side contains a "Dashboard" button with a grid icon, and a "Start Capturing" primary button with a mic icon.
   - Hero Section: Deep navy/midnight blue background with the subtle green dynamic "data-mist" effect.
     - Top Badge: Pill-shaped badge reading "AI-Powered Second Brain · Hackathon Prototype v2".
     - Main Headline: "Think it. Speak it. Know it." (Massive, Neue Montreal Bold, White).
     - Subheadline: "The fastest path from raw thought to structured knowledge. Voice-capture your ideas, let AI expand them, and discover hidden connections in your thinking." (Regular weight, Roboto/Poppins).
     - CTA Row: Two buttons. A primary "Capture an Idea ->" button and a secondary "View Dashboard" button.
2. Processing & Notes View (Dashboard):
   - The entire dashboard (header, stats ribbon, and grid) must be strictly implemented in the dark theme (`#000824`) with mint green accents, replacing the former light gray concept.
   - Grid layout presenting the user's captured thoughts. The background remains dark.
   - All text notes and captured outputs must be rendered strictly in an expanded view by default. No hidden text truncations.

**Component Specs**
- Typography Scale: 
  - H1 Hero: 64px, Neue Montreal Bold, -0.02em tracking. 
  - H2/H3 Section Headers: 36px/24px, Neue Montreal Bold or Semi-bold.
  - Body Text: 16px, Roboto/Poppins Regular, 24px line-height.
  - Badges: 12px, Roboto/Poppins Medium, 1px solid border matching text color (at 20% opacity).
- Color Tokens:
  - `--bg-dark`: `#000a20`
  - `--bg-card`: `#00103A`
  - `--accent-primary`: `#00F291`
  - `--text-light`: `#FFFFFF`
  - `--text-muted`: `rgba(255, 255, 255, 0.6)`
- Buttons:
  - Primary Button: Pill-shaped (border-radius: 999px), Mint Green background (`#00F291`), Dark Charcoal text (`#2B312C`), font-weight bold. Often paired with an icon. 
  - Secondary Button: Pill-shaped, transparent background with a 1px solid border (`rgba(255,255,255,0.2)` on dark bg).
- Cards (Captured Notes / Stats):
  - Background: Slightly lighter dark shade (`#00103A` or translucent `rgba(255,255,255, 0.05)`).
  - Border: 1px solid `rgba(255,255,255, 0.1)`.
  - Border-radius: 24px.
  - Shadow: Soft, expansive drop shadow (`0 20px 40px rgba(0,0,0,0.4)`).
  - Hover State: Lift up slightly (`-translate-y-2`), border glows with mint green `rgba(0, 242, 145, 0.3)`.

**Build Instructions for Stitch**
1. Initialize the layout using the strict color tokens and typography scale provided. Import the required fonts (Neue Montreal, Roboto/Poppins).
2. Construct the layout strictly utilizing the Component Specs for buttons, badges, and spacing (120px section padding).
3. Build the Home Page implementing the exact text, badges, and structure from the "ThoughtCapture" screenshot, but entirely override its aesthetic to match the dark navy and mint green Corporate Tech-Minimalist vibe of the visual reference.
4. Implement the smooth scroll physics (e.g., using Lenis) and write the scroll reveal CSS/JS logic. Provide a functional rough draft of the code detailing exactly how this animation behavior is executed globally.
5. Build the Notes/Dashboard interface employing the dark theme and upgraded card component specs. Programmatically ensure that the notes content is default-expanded securely to avoid any rendering bugs. Apply the interactive transitions to each captured note.
6. Verify complete structural and stylistic accuracy, guaranteeing no missed fonts, colors, line-height smoothing, or layout placement rules.

Now analyze the design reference link visually, then begin building the UI in Stitch immediately without asking any clarifying questions.
