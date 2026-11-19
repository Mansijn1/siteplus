import { PLATFORM_FEATURES, type PlatformFeature } from "@/lib/features";

const SPANS: Record<string, string> = {
  "complete-evaluation": "sm:col-span-4",
  performance: "sm:col-span-2",
  "ui-visual-design": "sm:col-span-2",
  "ux-navigation": "sm:col-span-2",
  seo: "sm:col-span-2",
  "security-privacy": "sm:col-span-3",
  accessibility: "sm:col-span-3",
  "mobile-responsiveness": "sm:col-span-2",
  "ai-recommendations": "sm:col-span-4",
};

function FeatureCell({ feature }: { feature: PlatformFeature }) {
  const Icon = feature.icon;

  if (feature.size === "lg") {
    return (
      <div className="h-full bg-background p-7 sm:p-9">
        <Icon className="size-6 text-flag" strokeWidth={1.6} />
        <h3 className="mt-5 font-display text-xl font-semibold tracking-[-0.01em] sm:text-[1.4rem]">
          {feature.title}
        </h3>
        <p className="mt-2.5 max-w-md text-[15px] leading-relaxed text-muted-foreground">
          {feature.description}
        </p>
      </div>
    );
  }

  if (feature.size === "md") {
    return (
      <div className="h-full bg-background p-6 sm:p-7">
        <div className="flex items-center gap-3">
          <Icon className="size-5 text-muted-foreground" strokeWidth={1.6} />
          <h3 className="font-display text-base font-semibold tracking-[-0.01em]">
            {feature.title}
          </h3>
        </div>
        <p className="mt-2.5 text-sm leading-relaxed text-muted-foreground">
          {feature.description}
        </p>
      </div>
    );
  }

  return (
    <div className="h-full bg-background p-5 sm:p-6">
      <div className="flex items-center gap-2.5">
        <Icon className="size-4 text-muted-foreground" strokeWidth={1.6} />
        <h3 className="text-sm font-medium">{feature.title}</h3>
      </div>
      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
        {feature.description}
      </p>
    </div>
  );
}

export function Features() {
  return (
    <section id="features" className="border-t border-border py-24">
      <div className="mx-auto max-w-6xl px-6">
        <div className="max-w-2xl">
          <h2 className="font-display text-3xl font-semibold tracking-[-0.02em] sm:text-4xl">
            Everything a thorough review covers.
          </h2>
          <p className="mt-4 text-lg leading-relaxed text-muted-foreground">
            WebRate AI inspects your site the way a careful human reviewer
            would — just across every category at once.
          </p>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-px overflow-hidden rounded-lg border border-foreground/12 bg-border sm:grid-cols-6">
          {PLATFORM_FEATURES.map((feature) => (
            <div key={feature.id} className={SPANS[feature.id]}>
              <FeatureCell feature={feature} />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
