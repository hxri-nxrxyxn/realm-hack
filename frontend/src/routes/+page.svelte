<script lang="ts">
	import { onMount, onDestroy } from "svelte";
	import { Button } from "#lib/components/ui/button/index.js";
	import { Badge } from "#lib/components/ui/badge/index.js";
	import { Switch } from "#lib/components/ui/switch/index.js";
	import * as Alert from "#lib/components/ui/alert/index.js";
	import * as Card from "#lib/components/ui/card/index.js";
	import { Separator } from "#lib/components/ui/separator/index.js";

	import MagnetometerCard from "#lib/components/MagnetometerCard.svelte";
	import PedometerCard from "#lib/components/PedometerCard.svelte";
	import AmbientLightCard from "#lib/components/AmbientLightCard.svelte";

	import { sensorManager } from "#lib/services/sensorManager.svelte.js";
	import {
		Play,
		Square,
		Smartphone,
		Globe,
		Radio,
		ShieldCheck,
		Wifi,
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

	let isSyncChecked = $derived(sensorManager.backendSyncEnabled);
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
						<Badge
							variant="outline"
							class={sensorManager.isNative
								? "border-emerald-500/40 bg-emerald-500/15 text-emerald-300 text-xs font-semibold px-2.5 py-0.5"
								: "border-blue-500/40 bg-blue-500/15 text-blue-300 text-xs font-semibold px-2.5 py-0.5"}
						>
							{#if sensorManager.isNative}
								<Smartphone class="mr-1 h-3.5 w-3.5 inline" /> Android
							{:else}
								<Globe class="mr-1 h-3.5 w-3.5 inline" /> Web Preview
							{/if}
						</Badge>
					</div>
					<p class="text-xs sm:text-sm text-muted-foreground truncate mt-0.5">
						Live Hardware Telemetry
					</p>
				</div>
			</div>

			<!-- Live Frequency Badge in Menu Bar -->
			<div class="flex items-center gap-2">
				{#if sensorManager.isListening}
					<div class="flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/15 px-3.5 py-1.5 text-xs sm:text-sm font-bold text-emerald-300 font-mono">
						<span class="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-ping"></span>
						<span>{sensorManager.updateRateHz} Hz</span>
					</div>
				{:else}
					<div class="flex items-center gap-2 rounded-full border border-border bg-secondary/80 px-3.5 py-1.5 text-xs sm:text-sm font-semibold text-muted-foreground">
						<span class="h-2.5 w-2.5 rounded-full bg-muted-foreground"></span>
						<span>Idle</span>
					</div>
				{/if}
			</div>
		</div>
	</header>

	<!-- Main Body Content -->
	<main class="mx-auto w-full max-w-5xl flex-1 px-3.5 sm:px-4 pt-4 sm:pt-6 space-y-5">
		<!-- Android Activity Permission Notice if needed -->
		{#if sensorManager.isNative && !sensorManager.status.hasActivityRecognitionPermission}
			<Alert.Root class="border-amber-500/40 bg-amber-500/15 text-amber-200 rounded-2xl">
				<ShieldCheck class="h-5 w-5 text-amber-400" />
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

				<!-- 4x1 Matrix (4 Columns x 1 Row) -->
				<div class="grid grid-cols-4 gap-2 sm:gap-3 pt-2 border-t border-border/50">
					<!-- Cell 1: Accelerometer -->
					<div class="flex flex-col items-center justify-center rounded-xl bg-secondary/60 p-2.5 ring-1 ring-border/50 text-center transition-colors group-hover:bg-secondary/80">
						<Activity class="h-4 w-4 text-sky-400 mb-1" />
						<div class="text-[10px] sm:text-xs font-bold text-foreground truncate w-full">Accel</div>
						<div class="text-[10px] text-sky-300 font-mono font-semibold mt-0.5 truncate w-full">
							{sensorManager.accelerometer.magnitude.toFixed(1)} m/s²
						</div>
					</div>

					<!-- Cell 2: Gyroscope -->
					<div class="flex flex-col items-center justify-center rounded-xl bg-secondary/60 p-2.5 ring-1 ring-border/50 text-center transition-colors group-hover:bg-secondary/80">
						<Compass class="h-4 w-4 text-violet-400 mb-1" />
						<div class="text-[10px] sm:text-xs font-bold text-foreground truncate w-full">Gyro</div>
						<div class="text-[10px] text-violet-300 font-mono font-semibold mt-0.5 truncate w-full">
							{sensorManager.gyroscope.rate.toFixed(1)} rad/s
						</div>
					</div>

					<!-- Cell 3: Compass -->
					<div class="flex flex-col items-center justify-center rounded-xl bg-secondary/60 p-2.5 ring-1 ring-border/50 text-center transition-colors group-hover:bg-secondary/80">
						<Zap class="h-4 w-4 text-rose-400 mb-1" />
						<div class="text-[10px] sm:text-xs font-bold text-foreground truncate w-full">Compass</div>
						<div class="text-[10px] text-rose-300 font-mono font-semibold mt-0.5 truncate w-full">
							{Math.round(sensorManager.magnetometer.heading)}° {sensorManager.magnetometer.cardinal}
						</div>
					</div>

					<!-- Cell 4: Photometer & Steps -->
					<div class="flex flex-col items-center justify-center rounded-xl bg-secondary/60 p-2.5 ring-1 ring-border/50 text-center transition-colors group-hover:bg-secondary/80">
						<SunMedium class="h-4 w-4 text-amber-400 mb-1" />
						<div class="text-[10px] sm:text-xs font-bold text-foreground truncate w-full">Light & Steps</div>
						<div class="text-[10px] text-amber-300 font-mono font-semibold mt-0.5 truncate w-full">
							{Math.round(sensorManager.ambientLight.lux)} lx
						</div>
					</div>
				</div>
			</Card.Root>
		</a>

		<!-- Telemetry & Stream Status Strip -->
		<div class="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border/60 bg-card/70 backdrop-blur-md p-3.5 sm:p-4 text-xs shadow-sm">
			<div class="flex items-center gap-3">
				<div class="flex items-center gap-2">
					<Radio class={sensorManager.isListening ? "h-4 w-4 text-emerald-400 animate-pulse" : "h-4 w-4 text-muted-foreground"} />
					<span class="text-sm font-bold text-foreground">
						{sensorManager.isListening ? "Live Stream Active" : "Stream Suspended"}
					</span>
				</div>
				<Separator orientation="vertical" class="h-4 hidden sm:block" />
				<div class="text-xs text-muted-foreground hidden sm:block">
					Buffer: <span class="text-foreground font-mono font-bold">25 points/sensor</span>
				</div>
			</div>

			<!-- Backend Relay Switch -->
			<div class="flex items-center gap-2.5">
				<Wifi class={sensorManager.backendSyncEnabled ? "h-4 w-4 text-primary" : "h-4 w-4 text-muted-foreground"} />
				<span class="text-xs font-medium text-muted-foreground">Server Relay:</span>
				<Switch
					checked={isSyncChecked}
					onCheckedChange={() => sensorManager.toggleBackendSync()}
				/>
				{#if sensorManager.backendSyncEnabled}
					<Badge
						variant="outline"
						class={sensorManager.syncStatus === "connected"
							? "border-emerald-500/30 text-emerald-300 text-[10px] font-bold"
							: "border-amber-500/30 text-amber-300 text-[10px] font-bold"}
					>
						{sensorManager.syncMessage || sensorManager.syncStatus}
					</Badge>
				{/if}
			</div>
		</div>

		<!-- The Only Start Sensors Button at the End -->
		<div class="pt-2 pb-4">
			<Card.Root class="overflow-hidden border-2 border-border/80 bg-gradient-to-b from-card to-card/60 rounded-3xl p-4 sm:p-6 shadow-xl text-center">
				<div class="max-w-md mx-auto space-y-3">
					<div>
						<h2 class="text-xl sm:text-2xl font-black tracking-tight text-foreground">
							{sensorManager.isListening ? "Sensor Telemetry Active" : "Sensors Stopped"}
						</h2>
						<p class="text-xs sm:text-sm text-muted-foreground mt-1">
							{sensorManager.isListening
								? "Hardware sensors are streaming live measurements."
								: "Tap below to resume live readings."}
						</p>
					</div>

					<!-- Single Start Sensors / Stop Sensors Button -->
					{#if sensorManager.isListening}
						<Button
							variant="destructive"
							class="w-full h-16 sm:h-18 text-lg sm:text-xl font-black rounded-2xl shadow-xl gap-3 transition-transform active:scale-[0.98] ring-4 ring-destructive/20 cursor-pointer"
							onclick={() => sensorManager.stop()}
						>
							<Square class="h-6 w-6 fill-current animate-pulse" />
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

					<div class="flex items-center justify-center gap-3 text-xs text-muted-foreground pt-1">
						<span class="flex items-center gap-1">
							<span class="h-1.5 w-1.5 rounded-full {sensorManager.isListening ? 'bg-emerald-400' : 'bg-muted-foreground'}"></span>
							{sensorManager.isListening ? 'Streaming' : 'Paused'}
						</span>
						<span>•</span>
						<span>Optimized for all screen sizes</span>
					</div>
				</div>
			</Card.Root>
		</div>
	</main>
</div>
