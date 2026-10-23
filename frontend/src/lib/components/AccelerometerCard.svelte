<script lang="ts">
	import * as Card from "#lib/components/ui/card/index.js";
	import { Badge } from "#lib/components/ui/badge/index.js";
	import Sparkline from "./Sparkline.svelte";
	import { sensorManager } from "#lib/services/sensorManager.svelte.js";
	import { Activity, Gauge } from "lucide-svelte";

	let isHighG = $derived(sensorManager.accelerometer.magnitude > 15);
	let gForce = $derived((sensorManager.accelerometer.magnitude / 9.80665).toFixed(2));
</script>

<Card.Root class="relative overflow-hidden border-border/70 bg-card/90 shadow-md backdrop-blur-xl transition-all hover:border-sky-500/40 rounded-2xl">
	<!-- Ambient glow -->
	<div class="pointer-events-none absolute -right-12 -top-12 h-36 w-36 rounded-full bg-sky-500/10 blur-2xl"></div>

	<Card.Header class="pb-2">
		<div class="flex items-center justify-between">
			<div class="flex items-center gap-3">
				<div class="flex h-11 w-11 items-center justify-center rounded-xl bg-sky-500/15 text-sky-400 ring-1 ring-sky-500/30 shadow-sm">
					<Activity class="h-6 w-6" />
				</div>
				<div>
					<Card.Title class="text-lg sm:text-xl font-bold tracking-tight">Accelerometer</Card.Title>
					<Card.Description class="text-xs text-muted-foreground">3-Axis Linear & Gravity</Card.Description>
				</div>
			</div>

			<Badge
				variant="outline"
				class={isHighG
					? "border-red-500/40 bg-red-500/20 text-red-300 text-xs font-semibold px-2.5 py-0.5 animate-pulse"
					: "border-sky-500/30 bg-sky-500/10 text-sky-300 text-xs font-medium px-2.5 py-0.5"}
			>
				{isHighG ? "High Impact" : `${gForce} G`}
			</Badge>
		</div>
	</Card.Header>

	<Card.Content class="space-y-5 pt-2">
		<!-- Giant Vector Magnitude Readout -->
		<div class="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
			<div>
				<div class="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
					Net Acceleration Force
				</div>
				<div class="flex items-baseline gap-2">
					<span class="text-5xl sm:text-6xl font-black tracking-tight text-foreground font-mono leading-none">
						{sensorManager.accelerometer.magnitude.toFixed(2)}
					</span>
					<span class="text-base font-semibold text-muted-foreground">m/s²</span>
				</div>
			</div>
			<div class="flex justify-end sm:justify-start">
				<Sparkline
					data={sensorManager.accelHistory}
					strokeColor="#38bdf8"
					fillColor="rgba(56, 189, 248, 0.15)"
					height={46}
					width={140}
				/>
			</div>
		</div>

		<!-- 3-Axis Balance Meters -->
		<div class="space-y-3 rounded-xl bg-secondary/40 p-3.5 ring-1 ring-border/40">
			<!-- X Axis -->
			<div class="space-y-1.5">
				<div class="flex justify-between items-center text-xs">
					<div class="flex items-center gap-1.5 font-semibold text-sky-400">
						<span class="h-2 w-2 rounded-full bg-sky-400"></span>
						<span>X-Axis (Lateral Tilt)</span>
					</div>
					<span class="font-mono font-bold text-foreground text-sm">
						{sensorManager.accelerometer.x > 0 ? "+" : ""}{sensorManager.accelerometer.x.toFixed(2)}
						<span class="text-[10px] text-muted-foreground font-normal">m/s²</span>
					</span>
				</div>
				<div class="relative h-2.5 w-full bg-secondary/80 rounded-full overflow-hidden flex items-center">
					<div class="absolute left-1/2 h-full w-0.5 bg-border z-10"></div>
					<div
						class="h-full bg-gradient-to-r from-sky-500 to-sky-400 transition-all duration-75 rounded-full"
						style:width={`${Math.min(100, Math.abs(sensorManager.accelerometer.x) * 8)}%`}
					></div>
				</div>
			</div>

			<!-- Y Axis -->
			<div class="space-y-1.5">
				<div class="flex justify-between items-center text-xs">
					<div class="flex items-center gap-1.5 font-semibold text-indigo-400">
						<span class="h-2 w-2 rounded-full bg-indigo-400"></span>
						<span>Y-Axis (Pitch / Surge)</span>
					</div>
					<span class="font-mono font-bold text-foreground text-sm">
						{sensorManager.accelerometer.y > 0 ? "+" : ""}{sensorManager.accelerometer.y.toFixed(2)}
						<span class="text-[10px] text-muted-foreground font-normal">m/s²</span>
					</span>
				</div>
				<div class="relative h-2.5 w-full bg-secondary/80 rounded-full overflow-hidden flex items-center">
					<div class="absolute left-1/2 h-full w-0.5 bg-border z-10"></div>
					<div
						class="h-full bg-gradient-to-r from-indigo-500 to-indigo-400 transition-all duration-75 rounded-full"
						style:width={`${Math.min(100, Math.abs(sensorManager.accelerometer.y) * 8)}%`}
					></div>
				</div>
			</div>

			<!-- Z Axis -->
			<div class="space-y-1.5">
				<div class="flex justify-between items-center text-xs">
					<div class="flex items-center gap-1.5 font-semibold text-cyan-400">
						<span class="h-2 w-2 rounded-full bg-cyan-400"></span>
						<span>Z-Axis (Vertical Gravity)</span>
					</div>
					<span class="font-mono font-bold text-foreground text-sm">
						{sensorManager.accelerometer.z > 0 ? "+" : ""}{sensorManager.accelerometer.z.toFixed(2)}
						<span class="text-[10px] text-muted-foreground font-normal">m/s²</span>
					</span>
				</div>
				<div class="relative h-2.5 w-full bg-secondary/80 rounded-full overflow-hidden flex items-center">
					<div class="absolute left-1/2 h-full w-0.5 bg-border z-10"></div>
					<div
						class="h-full bg-gradient-to-r from-cyan-500 to-cyan-400 transition-all duration-75 rounded-full"
						style:width={`${Math.min(100, Math.abs(sensorManager.accelerometer.z) * 8)}%`}
					></div>
				</div>
			</div>
		</div>
	</Card.Content>
</Card.Root>
