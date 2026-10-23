<script lang="ts">
	import { onMount, onDestroy } from "svelte";
	import { Button } from "#lib/components/ui/button/index.js";
	import * as Alert from "#lib/components/ui/alert/index.js";
	import * as Card from "#lib/components/ui/card/index.js";

	import MagnetometerCard from "#lib/components/MagnetometerCard.svelte";
	import PedometerCard from "#lib/components/PedometerCard.svelte";
	import AmbientLightCard from "#lib/components/AmbientLightCard.svelte";
	import SmsSenderCard from "#lib/components/SmsSenderCard.svelte";

	import { sensorManager } from "#lib/services/sensorManager.svelte.js";
	import {
		Play,
		Square,
		ShieldCheck,
		Activity,
		ChevronRight,
		Compass,
		Zap,
		SunMedium,
		Sliders
	} from "lucide-svelte";

	onMount(async () => {
		await sensorManager.initialize();
		await sensorManager.start();
	});

	onDestroy(() => {
		sensorManager.destroy();
	});
</script>

<div class="min-h-screen bg-background text-foreground flex flex-col pb-8">
	<!-- Enlarged Top Menu Bar with safe-area padding -->
	<header class="sticky top-0 z-40 border-b border-border/70 bg-background/95 backdrop-blur-xl px-4 sm:px-6 pt-safe pb-4 sm:pb-5 shadow-md">
		<div class="mx-auto flex max-w-5xl items-center justify-between gap-3">
			<div class="flex items-center gap-3.5 sm:gap-4">
				<div class="flex h-13 w-13 sm:h-15 sm:w-15 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-primary/80 text-primary-foreground shadow-lg ring-1 ring-primary/30">
					<Activity class="h-7 w-7 sm:h-8 sm:w-8" />
				</div>
				<div class="min-w-0">
					<div class="flex items-center gap-2.5 flex-wrap">
						<h1 class="text-xl sm:text-2xl md:text-3xl font-black tracking-tight truncate">Rakshak Sensors</h1>
						<span class="text-xs font-mono font-semibold text-emerald-400">
							{sensorManager.isNative ? "Android" : "Web Preview"}
						</span>
					</div>
					<p class="text-xs sm:text-sm text-muted-foreground truncate mt-0.5">
						Hardware Telemetry
					</p>
				</div>
			</div>

			<!-- Live Frequency Display in Menu Bar -->
			<div class="flex items-center shrink-0">
				<div class="flex items-baseline gap-1 font-mono text-right">
					<span class="text-2xl sm:text-3xl font-black text-emerald-400">
						{sensorManager.isListening ? sensorManager.updateRateHz : 0}
					</span>
					<span class="text-xs font-bold text-emerald-400/70">Hz</span>
				</div>
			</div>
		</div>
	</header>

	<!-- Main Body Content -->
	<main class="mx-auto w-full max-w-5xl flex-1 px-3.5 sm:px-4 pt-4 sm:pt-6 space-y-5">
		<!-- Android Activity Permission Notice if needed -->
		{#if sensorManager.isNative && !sensorManager.status.hasActivityRecognitionPermission}
			<Alert.Root class="border-emerald-600/40 bg-emerald-950/40 text-emerald-200 rounded-2xl">
				<ShieldCheck class="h-5 w-5 text-emerald-400" />
				<Alert.Title class="text-sm font-bold">Permission Required for Pedometer</Alert.Title>
				<Alert.Description class="text-xs mt-1">
					Activity Recognition permission is needed for Android hardware step tracking.
				</Alert.Description>
			</Alert.Root>
		{/if}

		<!-- Sensor Data Directly Below Menu Bar: ONLY Compass, Pedometer, and Light Meter -->
		<div class="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-5">
			<!-- 1. Compass (Magnetometer) -->
			<div class="col-span-1">
				<MagnetometerCard />
			</div>

			<!-- 2. Pedometer -->
			<div class="col-span-1">
				<PedometerCard />
			</div>

			<!-- 3. Light Meter -->
			<div class="col-span-1">
				<AmbientLightCard />
			</div>
		</div>

		<!-- See All Sensors in a 4x1 Matrix -->
		<a
			href="/sensors"
			class="group block transition-all duration-200 active:scale-[0.99] focus:outline-none"
			title="See All Sensors"
		>
			<Card.Root class="overflow-hidden border-2 border-primary/30 bg-gradient-to-r from-card via-card to-primary/5 rounded-2xl p-4 sm:p-5 shadow-lg transition-all group-hover:border-primary/60 group-hover:shadow-primary/10">
				<div class="flex items-center justify-between pb-3">
					<div class="flex items-center gap-2.5">
						<div class="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/15 text-primary">
							<Sliders class="h-4 w-4" />
						</div>
						<div>
							<h3 class="text-sm sm:text-base font-bold tracking-tight text-foreground group-hover:text-primary transition-colors">
								See All Sensors
							</h3>
							<p class="text-xs text-muted-foreground">
								Full 5-axis telemetry, angular rotation, diagnostics & more
							</p>
						</div>
					</div>

					<div class="flex items-center gap-1.5 text-xs font-bold text-primary bg-primary/10 px-3 py-1.5 rounded-xl border border-primary/20 group-hover:bg-primary/20 transition-all">
						<span>View Full Suite</span>
						<ChevronRight class="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
					</div>
				</div>

				<!-- 4x1 Matrix (4 Columns x 1 Row) in Unified Emerald Gradient -->
				<div class="grid grid-cols-4 gap-2 sm:gap-3 pt-2 border-t border-border/50">
					<!-- Cell 1: Accelerometer -->
					<div class="flex flex-col items-center justify-center rounded-xl bg-secondary/60 p-2.5 ring-1 ring-border/50 text-center transition-colors group-hover:bg-secondary/80">
						<Activity class="h-4 w-4 text-emerald-400 mb-1" />
						<div class="text-[10px] sm:text-xs font-bold text-foreground truncate w-full">Accel</div>
						<div class="text-[10px] text-emerald-300 font-mono font-semibold mt-0.5 truncate w-full">
							{sensorManager.accelerometer.magnitude.toFixed(1)} m/s²
						</div>
					</div>

					<!-- Cell 2: Gyroscope -->
					<div class="flex flex-col items-center justify-center rounded-xl bg-secondary/60 p-2.5 ring-1 ring-border/50 text-center transition-colors group-hover:bg-secondary/80">
						<Compass class="h-4 w-4 text-emerald-400 mb-1" />
						<div class="text-[10px] sm:text-xs font-bold text-foreground truncate w-full">Gyro</div>
						<div class="text-[10px] text-emerald-300 font-mono font-semibold mt-0.5 truncate w-full">
							{sensorManager.gyroscope.rate.toFixed(1)} rad/s
						</div>
					</div>

					<!-- Cell 3: Compass -->
					<div class="flex flex-col items-center justify-center rounded-xl bg-secondary/60 p-2.5 ring-1 ring-border/50 text-center transition-colors group-hover:bg-secondary/80">
						<Zap class="h-4 w-4 text-emerald-400 mb-1" />
						<div class="text-[10px] sm:text-xs font-bold text-foreground truncate w-full">Compass</div>
						<div class="text-[10px] text-emerald-300 font-mono font-semibold mt-0.5 truncate w-full">
							{Math.round(sensorManager.magnetometer.heading)}° {sensorManager.magnetometer.cardinal}
						</div>
					</div>

					<!-- Cell 4: Photometer & Steps -->
					<div class="flex flex-col items-center justify-center rounded-xl bg-secondary/60 p-2.5 ring-1 ring-border/50 text-center transition-colors group-hover:bg-secondary/80">
						<SunMedium class="h-4 w-4 text-emerald-400 mb-1" />
						<div class="text-[10px] sm:text-xs font-bold text-foreground truncate w-full">Light & Steps</div>
						<div class="text-[10px] text-emerald-300 font-mono font-semibold mt-0.5 truncate w-full">
							{Math.round(sensorManager.ambientLight.lux)} lx
						</div>
					</div>
				</div>
			</Card.Root>
		</a>

		<!-- Direct SMS Alert Box -->
		<SmsSenderCard />

		<!-- Single Start / Stop Button -->
		<div class="pt-2 pb-6">
			{#if sensorManager.isListening}
				<Button
					variant="destructive"
					class="w-full h-16 sm:h-18 text-lg sm:text-xl font-black rounded-2xl shadow-xl gap-3 transition-transform active:scale-[0.98] ring-4 ring-emerald-900/30 bg-emerald-950 border border-emerald-700/60 text-emerald-200 hover:bg-emerald-900 cursor-pointer"
					onclick={() => sensorManager.stop()}
				>
					<Square class="h-6 w-6 fill-current" />
					<span>Stop Sensors</span>
				</Button>
			{:else}
				<Button
					variant="default"
					class="w-full h-16 sm:h-18 text-lg sm:text-xl font-black rounded-2xl shadow-xl gap-3 bg-emerald-600 hover:bg-emerald-500 text-white transition-transform active:scale-[0.98] ring-4 ring-emerald-500/30 cursor-pointer"
					onclick={() => sensorManager.start()}
				>
					<Play class="h-6 w-6 fill-current" />
					<span>Start Sensors</span>
				</Button>
			{/if}
		</div>
	</main>
</div>
