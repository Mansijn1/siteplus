import { SiteHeader } from "@/components/landing/site-header";
import { Hero } from "@/components/landing/hero";
import { ProductPreview } from "@/components/landing/product-preview";
import { Features } from "@/components/landing/features";
import { HowItWorks } from "@/components/landing/how-it-works";
import { EvaluationCategories } from "@/components/landing/evaluation-categories";
import { FinalCta } from "@/components/landing/final-cta";
import { SiteFooter } from "@/components/landing/site-footer";

export default function Home() {
  return (
    <div className="flex flex-1 flex-col">
      <SiteHeader />
      <main className="flex-1">
        <Hero />
        <ProductPreview />
        <Features />
        <HowItWorks />
        <EvaluationCategories />
        <FinalCta />
      </main>
      <SiteFooter />
    </div>
  );
}
