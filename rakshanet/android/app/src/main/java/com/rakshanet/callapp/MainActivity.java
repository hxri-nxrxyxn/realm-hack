package com.rakshanet.callapp;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(DirectSmsPlugin.class);
        registerPlugin(DirectCallPlugin.class);
        super.onCreate(savedInstanceState);
    }
}
