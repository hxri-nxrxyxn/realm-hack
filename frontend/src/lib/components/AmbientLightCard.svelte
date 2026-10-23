<script lang="ts">
	import * as Card from "#lib/components/ui/card/index.js";
	import { Badge } from "#lib/components/ui/badge/index.js";
	import { Progress } from "#lib/components/ui/progress/index.js";
	import Sparkline from "./Sparkline.svelte";
	import { sensorManager } from "#lib/services/sensorManager.svelte.js";
	import { SunMedium } from "lucide-svelte";

	let luxProgress = $derived(
		Math.min(100, Math.round((Math.log10(Math.max(1, sensorManager.ambientLight.lux)) / 4) * 100))
	);
</script>

<Card.Root class="relative overflow-hidden border-border/70 bg-card/90 shadow-md backdrop-blur-xl transition-all hover:border-amber-500/40 rounded-2xl">
	<!-- Ambient glow -->
	<div class="pointer-events-none absolute -right-12 -top-12 h-36 w-36 rounded-full bg-amber-500/10 blur-2xl"></div>

	<Card.Header class="pb-2">
		<div class="flex items-center justify-between">
			<div class="flex items-center gap-3">
				<div class="flex h-11 w-11 items-center justify-center rounded-xl bg-amber-500/15 text-amber-400 ring-1 ring-amber-500/30 shadow-sm">
					<SunMedium class="h-6 w-6" />
				</div>
				<div>
					<Card.Title class="text-lg sm:text-xl font-bold tracking-tight">Ambient Light</Card.Title>
					<Card.Description class="text-xs text-muted-foreground">Photometer Illuminance</Card.Description>
				</div>
			</div>

			<Badge
				variant="outline"
				class="border-amber-500/30 bg-amber-500/10 text-amber-300 text-xs font-medium px-2.5 py-0.5"
			>
				{sensorManager.ambientLight.environment}
			</Badge>
		</div>
	</Card.Header>

	<Card.Content class="space-y-5 pt-2">
		<!-- Giant Lux Readout -->
		<div class="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
			<div>
				<div class="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
					Illuminance Flux
				</div>
				<div class="flex items-baseline gap-2">
					<span class="text-5xl sm:text-6xl font-black tracking-tight text-foreground font-mono leading-none">
						{Math.round(sensorManager.ambientLight.lux).toLocaleString()}
					</span>
					<span class="text-base font-semibold text-muted-foreground">lux</span>
				</div>
			</div>
			<div class="flex justify-end sm:justify-start">
				<Sparkline
					data={sensorManager.lightHistory}
					strokeColor="#f59e0b"
					fillColor="rgba(245, 158, 11, 0.15)"
					height={46}
					width={140}
				/>
			</div>
		</div>

		<!-- Light Intensity Meter -->
		<div class="space-y-2 rounded-xl bg-secondary/40 p-3 ring-1 ring-border/40">
			<div class="flex justify-between items-center text-xs">
				<span class="text-muted-foreground font-medium">Brightness Spectrum</span>
				<span class="font-bold text-amber-400 font-mono text-sm">{luxProgress}%</span>
			</div>
			<Progress value={luxProgress} class="h-2.5 bg-secondary/80" />
		</div>

		<!-- 3 Zone Indicators -->
		<div class="grid grid-cols-3 gap-2.5 pt-1 text-center">
			<div class="flex flex-col rounded-xl bg-secondary/60 p-2.5 ring-1 {sensorManager.ambientLight.lux < 50 ? 'ring-amber-500/60 bg-amber-500/10' : 'ring-border/50'}">
				<div class="text-[10px] text-muted-foreground uppercase font-semibold">Dark / Night</div>
				<div class="text-sm font-bold font-mono text-foreground mt-0.5">&lt;50 lx</div>
				<div class="text-[10px] {sensorManager.ambientLight.lux < 50 ? 'text-amber-400 font-bold' : 'text-muted-foreground'} mt-0.5">
					{sensorManager.ambientLight.lux < 50 ? "● Active" : "Inactive"}
				</div>
			</div>

			<div class="flex flex-col rounded-xl bg-secondary/60 p-2.5 ring-1 {sensorManager.ambientLight.lux >= 50 && sensorManager.ambientLight.lux <= 1000 ? 'ring-amber-500/60 bg-amber-500/10' : 'ring-border/50'}">
				<div class="text-[10px] text-muted-foreground uppercase font-semibold">Indoor Office</div>
				<div class="text-sm font-bold font-mono text-foreground mt-0.5">50-1000 lx</div>
				<div class="text-[10px] {sensorManager.ambientLight.lux >= 50 && sensorManager.ambientLight.lux <= 1000 ? 'text-amber-400 font-bold' : 'text-muted-foreground'} mt-0.5">
					{sensorManager.ambientLight.lux >= 50 && sensorManager.ambientLight.lux <= 1000 ? "● Active" : "Inactive"}
				</div>
			</div>

			<div class="flex flex-col rounded-xl bg-secondary/60 p-2.5 ring-1 {sensorManager.ambientLight.lux > 1000 ? 'ring-amber-500/60 bg-amber-500/10' : 'ring-border/50'}">
				<div class="text-[10px] text-muted-foreground uppercase font-semibold">Sunlight</div>
				<div class="text-sm font-bold font-mono text-foreground mt-0.5">&gt;1000 lx</div>
				<div class="text-[10px] {sensorManager.ambientLight.lux > 1000 ? 'text-amber-400 font-bold' : 'text-muted-foreground'} mt-0.5">
					{sensorManager.ambientLight.lux > 1000 ? "● Active" : "Inactive"}
				</div>
			</div>
		</div>
	</Card.Content>
</Card.Root>
