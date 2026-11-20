"use client";

import { Bar, BarChart, Cell, ResponsiveContainer, XAxis, YAxis, Tooltip } from "recharts";
import { EVALUATION_CATEGORIES } from "@/lib/categories";
import { getGradeInfo } from "@/lib/scoring";
import { useEvaluationData } from "./evaluation-data-provider";

const TAG_COLOR: Record<string, string> = {
  pass: "var(--pass)",
  flag: "var(--flag)",
  critical: "var(--critical)",
};

export function ScoreDistributionChart() {
  const { data: evaluationData } = useEvaluationData();

  const data = EVALUATION_CATEGORIES.map((category) => ({
    name: category.shortName,
    score: evaluationData.scores[category.id] ?? 0,
    tag: getGradeInfo(evaluationData.scores[category.id] ?? 0).tag,
  })).sort((a, b) => b.score - a.score);

  return (
    <div className="h-[420px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 28, bottom: 4, left: 4 }} barCategoryGap={10}>
          <XAxis type="number" domain={[0, 100]} hide />
          <YAxis
            type="category"
            dataKey="name"
            width={128}
            tickLine={false}
            axisLine={false}
            tick={{ fill: "var(--muted-foreground)", fontSize: 12, fontFamily: "var(--font-body)" }}
          />
          <Tooltip
            cursor={{ fill: "var(--secondary)" }}
            contentStyle={{
              background: "var(--popover)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              fontSize: 12,
              fontFamily: "var(--font-body)",
            }}
            formatter={(value) => [`${value} / 100`, "Score"]}
          />
          <Bar dataKey="score" radius={[0, 3, 3, 0]} maxBarSize={14}>
            {data.map((entry) => (
              <Cell key={entry.name} fill={TAG_COLOR[entry.tag]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
