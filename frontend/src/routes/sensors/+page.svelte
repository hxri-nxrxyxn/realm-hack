<script lang="ts">
	import { onMount, onDestroy } from "svelte";
	import { Button } from "#lib/components/ui/button/index.js";
	import { Badge } from "#lib/components/ui/badge/index.js";
	import { Switch } from "#lib/components/ui/switch/index.js";
	import * as Alert from "#lib/components/ui/alert/index.js";
	import * as Card from "#lib/components/ui/card/index.js";
	import { Separator } from "#lib/components/ui/separator/index.js";

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
		Smartphone,
		Globe,
		Radio,
		ShieldCheck,
		Wifi,
		Sliders,
		ArrowLeft
	} from "lucide-svelte";

	onMount(async () => {
		await sensorManager.initialize();
		if (!sensorManager.isListening) {
			await sensorManager.start();
		}
	});

	let isSyncChecked = $derived(sensorManager.backendSyncEnabled);
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
						Full Hardware Suite Telemetry
					</p>
				</div>
			</div>

			<!-- Live Frequency Pill in Menu Bar -->
			<div class="flex items-center shrink-0">
				{#if sensorManager.isListening}
					<div class="inline-flex items-center gap-2 rounded-full border border-emerald-500/40 bg-emerald-500/15 px-3.5 sm:px-4 py-1.5 text-xs sm:text-sm font-bold text-emerald-300 font-mono whitespace-nowrap shadow-sm ring-1 ring-emerald-500/20">
						<span class="relative flex h-2.5 w-2.5 shrink-0">
							<span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
							<span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
						</span>
						<span class="whitespace-nowrap tracking-wide">{sensorManager.updateRateHz} Hz</span>
					</div>
				{:else}
					<div class="inline-flex items-center gap-2 rounded-full border border-border bg-secondary/80 px-3.5 sm:px-4 py-1.5 text-xs sm:text-sm font-semibold text-muted-foreground font-mono whitespace-nowrap shadow-sm">
						<span class="h-2 w-2 rounded-full bg-muted-foreground/60 shrink-0"></span>
						<span class="whitespace-nowrap tracking-wide">0 Hz</span>
					</div>
				{/if}
			</div>
		</div>
	</header>

	<!-- Main Body Content: All Sensors Grid Directly Below Menu Bar -->
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
						<Badge variant="outline" class="text-[10px] border-primary/40 bg-primary/10 text-primary font-bold">Capacitor 7</Badge>
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
							<span class="font-mono font-bold text-sky-400">{sensorManager.updateRateHz} updates/sec</span>
						</div>
					</div>
				</div>

				<div class="pt-3 border-t border-border/50 mt-3 text-center">
					<span class="text-[11px] text-muted-foreground font-medium">Automatic continuous sensor synchronization</span>
				</div>
			</div>
		</div>

		<!-- Direct SMS Alert Box -->
		<SmsSenderCard />

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

		<!-- Single Start Sensors / Stop Sensors Button at the End -->
		<div class="pt-2 pb-4">
			<Card.Root class="overflow-hidden border-2 border-border/80 bg-gradient-to-b from-card to-card/60 rounded-3xl p-4 sm:p-6 shadow-xl text-center">
				<div class="max-w-md mx-auto space-y-3">
					<div>
						<h2 class="text-xl sm:text-2xl font-black tracking-tight text-foreground">
							{sensorManager.isListening ? "Sensor Telemetry Active" : "Sensors Stopped"}
						</h2>
						<p class="text-xs sm:text-sm text-muted-foreground mt-1">
							{sensorManager.isListening
								? "All 5 sensors are streaming live measurements at high frequency."
								: "Tap below to resume live readings for pedometer, gyro, magnet, accel, and light."}
						</p>
					</div>

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
