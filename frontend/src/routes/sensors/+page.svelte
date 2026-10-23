<script lang="ts">
	import { onMount, onDestroy } from "svelte";
	import { Button } from "#lib/components/ui/button/index.js";
	import * as Alert from "#lib/components/ui/alert/index.js";

	import PedometerCard from "#lib/components/PedometerCard.svelte";
	import AccelerometerCard from "#lib/components/AccelerometerCard.svelte";
	import GyroscopeCard from "#lib/components/GyroscopeCard.svelte";
	import MagnetometerCard from "#lib/components/MagnetometerCard.svelte";
	import AmbientLightCard from "#lib/components/AmbientLightCard.svelte";
	import SmsSenderCard from "#lib/components/SmsSenderCard.svelte";

	import { sensorManager } from "#lib/services/sensorManager.svelte.js";
	import {
		Play,
		Square,
		ShieldCheck,
		Sliders,
		ArrowLeft
	} from "lucide-svelte";

	onMount(async () => {
		await sensorManager.initialize();
		if (!sensorManager.isListening) {
			await sensorManager.start();
		}
	});
</script>

<div class="min-h-screen bg-background text-foreground flex flex-col pb-8">
	<!-- Enlarged Top Menu Bar with Back Button -->
	<header class="sticky top-0 z-40 border-b border-border/70 bg-background/95 backdrop-blur-xl px-4 sm:px-6 pt-safe pb-4 sm:pb-5 shadow-md">
		<div class="mx-auto flex max-w-5xl items-center justify-between gap-3">
			<div class="flex items-center gap-3 sm:gap-4">
				<a
					href="/"
					class="flex h-11 w-11 sm:h-12 sm:w-12 shrink-0 items-center justify-center rounded-2xl bg-secondary/80 text-foreground ring-1 ring-border/60 hover:bg-secondary transition-all active:scale-95"
					title="Back to Home"
				>
					<ArrowLeft class="h-6 w-6" />
				</a>

				<div class="min-w-0">
					<div class="flex items-center gap-2.5 flex-wrap">
						<h1 class="text-xl sm:text-2xl md:text-3xl font-black tracking-tight truncate">All Sensors</h1>
						<span class="text-xs font-mono font-semibold text-emerald-400">
							{sensorManager.isNative ? "Android" : "Web Preview"}
						</span>
					</div>
					<p class="text-xs sm:text-sm text-muted-foreground truncate mt-0.5">
						Hardware Telemetry Suite
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

	<!-- Main Body Content: All Sensors Grid Directly Below Menu Bar -->
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

		<!-- All Sensors Data Grid Directly Below Menu Bar -->
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
			<!-- Pedometer -->
			<div class="col-span-1 md:col-span-2 lg:col-span-1">
				<PedometerCard />
			</div>

			<!-- Accelerometer -->
			<div class="col-span-1">
				<AccelerometerCard />
			</div>

			<!-- Gyroscope -->
			<div class="col-span-1">
				<GyroscopeCard />
			</div>

			<!-- Magnetometer -->
			<div class="col-span-1">
				<MagnetometerCard />
			</div>

			<!-- Ambient Light -->
			<div class="col-span-1">
				<AmbientLightCard />
			</div>

			<!-- Hardware Diagnostic Card -->
			<div class="col-span-1 flex flex-col justify-between rounded-2xl border border-border/70 bg-card/90 p-4 sm:p-5 shadow-md backdrop-blur-xl">
				<div>
					<div class="flex items-center justify-between pb-2">
						<div class="flex items-center gap-2">
							<Sliders class="h-4 w-4 text-primary" />
							<span class="text-xs font-bold uppercase tracking-wider text-foreground">Hardware Status</span>
						</div>
						<span class="text-xs font-mono font-semibold text-emerald-400">Capacitor 7</span>
					</div>
					<p class="text-xs text-muted-foreground mt-1">
						Package: <span class="font-mono text-foreground font-semibold">net.rakshak.sensors</span>
					</p>

					<div class="mt-3.5 space-y-2 text-xs">
						<div class="flex justify-between items-center rounded-lg bg-secondary/50 px-2.5 py-1.5">
							<span class="text-muted-foreground">Platform Engine:</span>
							<span class="font-mono font-bold text-foreground">{sensorManager.isNative ? "Android Native" : "Web Preview"}</span>
						</div>
						<div class="flex justify-between items-center rounded-lg bg-secondary/50 px-2.5 py-1.5">
							<span class="text-muted-foreground">Step Detector:</span>
							<span class="font-mono font-bold text-emerald-400">{sensorManager.status.pedometerHardwareAvailable ? "Hardware" : "Software"}</span>
						</div>
						<div class="flex justify-between items-center rounded-lg bg-secondary/50 px-2.5 py-1.5">
							<span class="text-muted-foreground">Update Rate:</span>
							<span class="font-mono font-bold text-emerald-400">{sensorManager.updateRateHz} updates/sec</span>
						</div>
					</div>
				</div>

				<div class="pt-3 border-t border-border/50 mt-3 text-center">
					<span class="text-[11px] text-muted-foreground font-medium">Continuous synchronization</span>
				</div>
			</div>
		</div>

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
