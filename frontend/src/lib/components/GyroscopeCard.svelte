<script lang="ts">
	import * as Card from "#lib/components/ui/card/index.js";
	import { Badge } from "#lib/components/ui/badge/index.js";
	import Sparkline from "./Sparkline.svelte";
	import { sensorManager } from "#lib/services/sensorManager.svelte.js";
	import { Compass } from "lucide-svelte";

	let isSpinning = $derived(sensorManager.gyroscope.rate > 0.8);
	let degPerSec = $derived(Math.round(sensorManager.gyroscope.rate * (180 / Math.PI)));
</script>

<Card.Root class="relative overflow-hidden border-border/70 bg-card/90 shadow-md backdrop-blur-xl transition-all hover:border-emerald-500/40 rounded-2xl">
	<!-- Ambient glow -->
	<div class="pointer-events-none absolute -right-12 -top-12 h-36 w-36 rounded-full bg-emerald-500/10 blur-2xl"></div>

	<Card.Header class="pb-2">
		<div class="flex items-center justify-between">
			<div class="flex items-center gap-3">
				<div class="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-500/15 text-emerald-400 ring-1 ring-emerald-500/30 shadow-sm">
					<Compass class="h-6 w-6" />
				</div>
				<div>
					<Card.Title class="text-lg sm:text-xl font-bold tracking-tight">Gyroscope</Card.Title>
					<Card.Description class="text-xs text-muted-foreground">Angular Velocity & Rotation</Card.Description>
				</div>
			</div>

			<Badge
				variant="outline"
				class={isSpinning
					? "border-emerald-400/50 bg-emerald-500/15 text-emerald-200 text-xs font-semibold px-2.5 py-0.5"
					: "border-border bg-secondary/60 text-muted-foreground text-xs font-medium px-2.5 py-0.5"}
			>
				{isSpinning ? "Active Spin" : "Stationary"}
			</Badge>
		</div>
	</Card.Header>

	<Card.Content class="space-y-5 pt-2">
		<!-- Giant Angular Speed Readout -->
		<div class="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
			<div>
				<div class="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
					Angular Velocity Speed
				</div>
				<div class="flex items-baseline gap-2">
					<span class="text-5xl sm:text-6xl font-black tracking-tight text-foreground font-mono leading-none">
						{sensorManager.gyroscope.rate.toFixed(2)}
					</span>
					<span class="text-base font-semibold text-muted-foreground">rad/s</span>
					<span class="text-xs font-bold font-mono text-emerald-400 ml-1">({degPerSec}°/s)</span>
				</div>
			</div>
			<div class="flex justify-end sm:justify-start">
				<Sparkline
					data={sensorManager.gyroHistory}
					strokeColor="#10b981"
					fillColor="rgba(16, 185, 129, 0.15)"
					height={46}
					width={140}
				/>
			</div>
		</div>

		<!-- 3-Axis Rotation Cards in Shades of Green -->
		<div class="grid grid-cols-3 gap-2.5 pt-1">
			<!-- Pitch X -->
			<div class="flex flex-col rounded-xl bg-secondary/60 p-3 ring-1 ring-border/50 text-center">
				<div class="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider mb-1">
					Pitch (X)
				</div>
				<div class="text-lg sm:text-xl font-bold font-mono text-foreground">
					{sensorManager.gyroscope.x > 0 ? "+" : ""}{sensorManager.gyroscope.x.toFixed(2)}
				</div>
				<div class="text-[10px] text-muted-foreground uppercase font-medium mt-0.5">rad/s</div>
			</div>

			<!-- Roll Y -->
			<div class="flex flex-col rounded-xl bg-secondary/60 p-3 ring-1 ring-border/50 text-center">
				<div class="text-[11px] font-semibold text-teal-400 uppercase tracking-wider mb-1">
					Roll (Y)
				</div>
				<div class="text-lg sm:text-xl font-bold font-mono text-foreground">
					{sensorManager.gyroscope.y > 0 ? "+" : ""}{sensorManager.gyroscope.y.toFixed(2)}
				</div>
				<div class="text-[10px] text-muted-foreground uppercase font-medium mt-0.5">rad/s</div>
			</div>

			<!-- Yaw Z -->
			<div class="flex flex-col rounded-xl bg-secondary/60 p-3 ring-1 ring-border/50 text-center">
				<div class="text-[11px] font-semibold text-green-400 uppercase tracking-wider mb-1">
					Yaw (Z)
				</div>
				<div class="text-lg sm:text-xl font-bold font-mono text-foreground">
					{sensorManager.gyroscope.z > 0 ? "+" : ""}{sensorManager.gyroscope.z.toFixed(2)}
				</div>
				<div class="text-[10px] text-muted-foreground uppercase font-medium mt-0.5">rad/s</div>
			</div>
		</div>
	</Card.Content>
</Card.Root>
