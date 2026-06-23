---
name: Ephemeral Epicure Light
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#5b403f'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#8f6f6e'
  outline-variant: '#e4bebc'
  surface-tint: '#bb162c'
  primary: '#b7122a'
  on-primary: '#ffffff'
  primary-container: '#db313f'
  on-primary-container: '#fffbff'
  inverse-primary: '#ffb3b1'
  secondary: '#545f73'
  on-secondary: '#ffffff'
  secondary-container: '#d5e0f8'
  on-secondary-container: '#586377'
  tertiary: '#585d60'
  on-tertiary: '#ffffff'
  tertiary-container: '#707579'
  on-tertiary-container: '#fbfcff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ffdad8'
  primary-fixed-dim: '#ffb3b1'
  on-primary-fixed: '#410007'
  on-primary-fixed-variant: '#92001c'
  secondary-fixed: '#d8e3fb'
  secondary-fixed-dim: '#bcc7de'
  on-secondary-fixed: '#111c2d'
  on-secondary-fixed-variant: '#3c475a'
  tertiary-fixed: '#dfe3e7'
  tertiary-fixed-dim: '#c3c7cb'
  on-tertiary-fixed: '#171c1f'
  on-tertiary-fixed-variant: '#43474b'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  display-lg:
    fontFamily: Outfit
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Outfit
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Outfit
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Outfit
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Outfit
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Outfit
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Outfit
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 64px
---

## Brand & Style
The design system embodies the essence of "Ephemeral Epicure"—a premium, high-end culinary experience that is both fleeting and unforgettable. The target audience consists of discerning food enthusiasts and luxury travelers who value aesthetics as much as substance.

The design style is a **Luminous Glassmorphism**. It leverages the clarity of a light theme to create a sense of "aired luxury." By combining a clean, minimalist foundation with translucent, frosted-glass overlays and soft background blurs, the UI feels lightweight, ethereal, and sophisticated. The interface should evoke an emotional response of refined excitement and pristine quality.

## Colors
The palette is centered around the signature **Epicure Red (#E23744)**, adjusted to maintain high energy against light backgrounds. 

- **Primary (#E23744):** Used for key actions, brand moments, and critical highlights.
- **Secondary (#1E293B):** A deep slate used for high-contrast typography and iconography to ensure maximum legibility.
- **Tertiary (#F1F5F9):** A soft, cool gray used for subtle section backgrounds and decorative elements.
- **Neutral (#64748B):** Reserved for secondary text and disabled states.

Glassmorphic elements utilize a white-tinted translucency (`rgba(255, 255, 255, 0.7)`) with a high saturation backdrop filter to keep the underlying colors vibrant but diffused.

## Typography
This design system utilizes **Outfit** across all levels to maintain a geometric, modern, and clean aesthetic. 

Large display titles should use tighter letter spacing and bold weights to command attention. Body text is optimized for readability with generous line heights. Labels and small captions use a slightly increased letter spacing and higher weights to ensure they remain legible even when placed over semi-transparent glass layers.

## Layout & Spacing
The layout follows a **fluid grid** philosophy that prioritizes whitespace to evoke a premium feel. 

- **Desktop:** 12-column grid with 24px gutters and 64px outer margins. Content is often centered with significant lateral breathing room.
- **Mobile:** 4-column grid with 16px gutters and 16px margins. 
- **Rhythm:** All spacing (padding, margins, gaps) must be a multiple of the 4px base unit. Use `lg` (24px) for most container padding and `xl` (40px) for vertical section spacing to maintain an airy atmosphere.

## Elevation & Depth
Depth is achieved through **Glassmorphism and Ambient Shadows**. 

Instead of traditional heavy shadows, this design system uses:
1.  **Backdrop Blurs:** 12px to 20px blur applied to surfaces with a 70% white fill.
2.  **Inner Strokes:** A 1px solid white border at 40% opacity on glass elements to simulate a "beveled edge" light catch.
3.  **Soft Shadows:** Extremely diffused shadows using the primary or secondary color tinted at very low opacities (e.g., `rgba(30, 41, 59, 0.04)`).
4.  **Tonal Layering:** Surfaces "lift" by becoming more opaque and gaining a slightly more pronounced, yet still soft, shadow.

## Shapes
The shape language is consistently **Rounded (8px base)**. This provides a friendly yet structured feel that complements the geometric nature of the typography.

- **Standard Buttons & Inputs:** 8px (`0.5rem`)
- **Cards & Modals:** 16px (`1rem`)
- **Large Sections/Feature Blocks:** 24px (`1.5rem`)
- **Pills/Tags:** Full radius (capsule) for distinct visual separation from interactive buttons.

## Components
- **Buttons:** Primary buttons use the Epicure Red (#E23744) with white text. Secondary buttons are glassmorphic: semi-transparent white background with a 1px slate border and slate text.
- **Cards:** Glassmorphic containers with 16px rounded corners. They must have a subtle 1px white inner border to define their edges against light backgrounds.
- **Input Fields:** Off-white backgrounds (#F1F5F9) with 8px rounding. On focus, the border transitions to Epicure Red with a soft glow effect.
- **Chips/Tags:** Small capsule shapes. Use tertiary gray backgrounds for category tags and a light tint of the primary red for "Active" or "Featured" states.
- **Lists:** Clean, borderless list items separated by generous whitespace and subtle 1px dividers in Tertiary color.
- **Navigation:** Top navigation bars should be highly translucent with a strong backdrop blur, ensuring content remains visible but legible as it scrolls underneath.