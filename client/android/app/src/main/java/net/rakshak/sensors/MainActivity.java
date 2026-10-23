package net.rakshak.sensors;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(RakshakSensorsPlugin.class);
        registerPlugin(DirectSmsPlugin.class);
        super.onCreate(savedInstanceState);
    }
}
