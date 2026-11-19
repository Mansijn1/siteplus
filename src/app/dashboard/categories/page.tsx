import { Suspense } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { EVALUATION_CATEGORIES, type CategoryId } from "@/lib/categories";
import { CategoryPickerList } from "@/components/dashboard/category-picker-list";
import { CategoryDetail } from "@/components/dashboard/category-detail";

const VALID_IDS = new Set(EVALUATION_CATEGORIES.map((c) => c.id));

function resolveCategoryId(id: string | undefined): CategoryId {
  if (id && VALID_IDS.has(id as CategoryId)) return id as CategoryId;
  return EVALUATION_CATEGORIES[0].id;
}

async function CategoryAnalysisContent({
  searchParams,
}: {
  searchParams: Promise<{ id?: string }>;
}) {
  const { id } = await searchParams;
  const selectedId = resolveCategoryId(id);

  return (
    <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
      <CategoryPickerList selectedId={selectedId} />
      <CategoryDetail categoryId={selectedId} />
    </div>
  );
}

export default function CategoryAnalysisPage({
  searchParams,
}: {
  searchParams: Promise<{ id?: string }>;
}) {
  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-8 sm:px-6 lg:py-10">
      <div>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="size-3.5" />
          Back to Overview
        </Link>
        <h1 className="mt-3 font-display text-2xl font-semibold tracking-[-0.01em]">Category Analysis</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Select a category to see what was evaluated, what&apos;s working, and what to fix.
        </p>
      </div>

      <Suspense fallback={<div className="h-[600px]" />}>
        <CategoryAnalysisContent searchParams={searchParams} />
      </Suspense>
    </div>
  );
}
