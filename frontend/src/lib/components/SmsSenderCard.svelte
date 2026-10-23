<script lang="ts">
	import * as Card from "#lib/components/ui/card/index.js";
	import { Input } from "#lib/components/ui/input/index.js";
	import { Textarea } from "#lib/components/ui/textarea/index.js";
	import { Button } from "#lib/components/ui/button/index.js";
	import { Badge } from "#lib/components/ui/badge/index.js";
	import { sendSms } from "#lib/services/smsService.js";
	import { sensorManager } from "#lib/services/sensorManager.svelte.js";
	import { Send, MessageSquare, Phone, CheckCircle2, AlertCircle, Sparkles } from "lucide-svelte";

	let phoneNumber = $state("9995283835");
	let message = $state("🚨 Rakshak Alert: Live sensor detection active. Steps: 0, Heading: N");
	let isSending = $state(false);
	let status = $state<{ type: "success" | "error"; text: string } | null>(null);

	function appendSensorTelemetry() {
		const steps = sensorManager.pedometer.steps;
		const heading = Math.round(sensorManager.magnetometer.heading);
		const cardinal = sensorManager.magnetometer.cardinal;
		const accel = sensorManager.accelerometer.magnitude.toFixed(1);
		const lux = Math.round(sensorManager.ambientLight.lux);

		message = `🚨 Rakshak Alert: Steps: ${steps} | Heading: ${heading}° ${cardinal} | Accel: ${accel} m/s² | Lux: ${lux} lx`;
	}

	async function handleSend() {
		if (isSending) return;
		isSending = true;
		status = null;

		const result = await sendSms(phoneNumber, message);
		isSending = false;

		if (result.success) {
			status = { type: "success", text: result.message };
		} else {
			status = { type: "error", text: result.message };
		}

		// Auto dismiss status after 5s
		setTimeout(() => {
			if (status?.type === "success") {
				status = null;
			}
		}, 5000);
	}
</script>

<Card.Root class="relative overflow-hidden border-border/70 bg-card/90 shadow-md backdrop-blur-xl transition-all hover:border-primary/40 rounded-2xl">
	<!-- Subtle ambient glow -->
	<div class="pointer-events-none absolute -right-12 -top-12 h-36 w-36 rounded-full bg-primary/10 blur-2xl"></div>

	<Card.Header class="pb-3">
		<div class="flex items-center justify-between">
			<div class="flex items-center gap-3">
				<div class="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/15 text-primary ring-1 ring-primary/30 shadow-sm">
					<MessageSquare class="h-6 w-6" />
				</div>
				<div>
					<Card.Title class="text-lg sm:text-xl font-bold tracking-tight">Direct SMS Alert</Card.Title>
					<Card.Description class="text-xs text-muted-foreground">Send real-time alerts & coordinates</Card.Description>
				</div>
			</div>

			<Badge variant="outline" class="border-primary/30 bg-primary/10 text-primary text-xs font-semibold px-2.5 py-0.5">
				SMS Relay
			</Badge>
		</div>
	</Card.Header>

	<Card.Content class="space-y-4 pt-1">
		<!-- Phone Number Input -->
		<div class="space-y-1.5">
			<label for="sms-phone-input" class="text-xs font-semibold text-foreground flex items-center justify-between">
				<span class="flex items-center gap-1.5">
					<Phone class="h-3.5 w-3.5 text-muted-foreground" />
					Recipient Phone Number
				</span>
				<span class="text-[11px] text-muted-foreground font-normal">Default: 9995283835</span>
			</label>
			<div class="relative">
				<Input
					id="sms-phone-input"
					type="tel"
					placeholder="Enter 10-digit phone number"
					bind:value={phoneNumber}
					class="h-11 rounded-xl bg-secondary/50 border-border/70 text-foreground font-mono font-medium pl-3 pr-4 text-sm focus:border-primary"
				/>
			</div>
		</div>

		<!-- Message Text Area Input -->
		<div class="space-y-1.5">
			<div class="flex items-center justify-between">
				<label for="sms-message-input" class="text-xs font-semibold text-foreground flex items-center gap-1.5">
					<MessageSquare class="h-3.5 w-3.5 text-muted-foreground" />
					Message Content
				</label>
				<button
					type="button"
					class="text-[11px] font-semibold text-primary hover:text-primary/80 flex items-center gap-1 cursor-pointer transition-colors"
					onclick={appendSensorTelemetry}
				>
					<Sparkles class="h-3 w-3" />
					Auto-fill Telemetry
				</button>
			</div>
			<Textarea
				id="sms-message-input"
				rows={3}
				placeholder="Type message content here..."
				bind:value={message}
				class="rounded-xl bg-secondary/50 border-border/70 text-foreground text-xs sm:text-sm resize-none focus:border-primary p-3"
			/>
		</div>

		<!-- Feedback Status Alert Banner -->
		{#if status}
			<div
				class={`flex items-center gap-2 rounded-xl p-3 text-xs font-semibold border ${
					status.type === "success"
						? "bg-emerald-500/15 border-emerald-500/40 text-emerald-300"
						: "bg-destructive/15 border-destructive/40 text-destructive-foreground"
				}`}
			>
				{#if status.type === "success"}
					<CheckCircle2 class="h-4 w-4 shrink-0 text-emerald-400" />
				{:else}
					<AlertCircle class="h-4 w-4 shrink-0 text-red-400" />
				{/if}
				<span class="truncate">{status.text}</span>
			</div>
		{/if}

		<!-- Send SMS Button -->
		<Button
			class="w-full h-11 text-sm font-bold rounded-xl gap-2 transition-all active:scale-[0.98] shadow-md cursor-pointer"
			disabled={isSending}
			onclick={handleSend}
		>
			<Send class="h-4 w-4" />
			<span>{isSending ? "Sending SMS..." : "Send SMS Now"}</span>
		</Button>
	</Card.Content>
</Card.Root>
