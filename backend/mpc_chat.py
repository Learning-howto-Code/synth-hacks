"""
Mac-to-Mac chat over Apple MultipeerConnectivity (MPC).

Run on two Macs on the same Wi-Fi / Bluetooth range:

    python mpc_chat.py --name Jake
    python mpc_chat.py --name Shree

Each peer both advertises and browses, auto-invites discovered peers,
auto-accepts invitations, and forwards stdin lines as UTF-8 messages.

Requires:
    pip install pyobjc-framework-MultipeerConnectivity

Notes:
    - serviceType must be 1-15 chars, lowercase ASCII letters/digits/hyphens.
    - First run prompts macOS for Local Network permission; allow it.
"""

import argparse
import sys
import threading

import objc
from Foundation import NSObject, NSData, NSRunLoop, NSDate
from MultipeerConnectivity import (
    MCPeerID,
    MCSession,
    MCNearbyServiceAdvertiser,
    MCNearbyServiceBrowser,
    MCEncryptionRequired,
    MCSessionStateNotConnected,
    MCSessionStateConnecting,
    MCSessionStateConnected,
)


STATE_NAMES = {
    MCSessionStateNotConnected: "NotConnected",
    MCSessionStateConnecting: "Connecting",
    MCSessionStateConnected: "Connected",
}


class MPCDelegate(NSObject):
    """Single delegate object for session + advertiser + browser."""

    def initWithPeer_service_(self, peer_id, service_type):
        self = objc.super(MPCDelegate, self).init()
        if self is None:
            return None
        self.peer_id = peer_id
        self.service_type = service_type
        self.session = MCSession.alloc().initWithPeer_securityIdentity_encryptionPreference_(
            peer_id, None, MCEncryptionRequired
        )
        self.session.setDelegate_(self)
        self.advertiser = MCNearbyServiceAdvertiser.alloc().initWithPeer_discoveryInfo_serviceType_(
            peer_id, None, service_type
        )
        self.advertiser.setDelegate_(self)
        self.browser = MCNearbyServiceBrowser.alloc().initWithPeer_serviceType_(
            peer_id, service_type
        )
        self.browser.setDelegate_(self)
        return self

    def start(self):
        self.advertiser.startAdvertisingPeer()
        self.browser.startBrowsingForPeers()
        print(f"[mpc] advertising + browsing as {self.peer_id.displayName()!r} on '{self.service_type}'")

    def stop(self):
        self.advertiser.stopAdvertisingPeer()
        self.browser.stopBrowsingForPeers()
        self.session.disconnect()

    def send_text(self, text):
        peers = list(self.session.connectedPeers())
        if not peers:
            print("[mpc] no connected peers; message dropped")
            return
        data = NSData.dataWithBytes_length_(text.encode("utf-8"), len(text.encode("utf-8")))
        ok, err = self.session.sendData_toPeers_withMode_error_(data, peers, 0, None)
        if not ok:
            print(f"[mpc] send failed: {err}")

    # --- MCSessionDelegate ---

    def session_peer_didChangeState_(self, session, peer, state):
        print(f"[session] {peer.displayName()} -> {STATE_NAMES.get(state, state)}")

    def session_didReceiveData_fromPeer_(self, session, data, peer):
        try:
            text = bytes(data).decode("utf-8")
        except UnicodeDecodeError:
            text = repr(bytes(data))
        print(f"\n[{peer.displayName()}] {text}\n> ", end="", flush=True)

    def session_didReceiveStream_withName_fromPeer_(self, session, stream, name, peer):
        pass

    def session_didStartReceivingResourceWithName_fromPeer_withProgress_(self, session, name, peer, progress):
        pass

    def session_didFinishReceivingResourceWithName_fromPeer_atURL_withError_(self, session, name, peer, url, err):
        pass

    def session_didReceiveCertificate_fromPeer_certificateHandler_(self, session, cert, peer, handler):
        # Accept all certificates (encryption still required by session config).
        handler(True)

    # --- MCNearbyServiceAdvertiserDelegate ---

    def advertiser_didReceiveInvitationFromPeer_withContext_invitationHandler_(
        self, advertiser, peer, context, handler
    ):
        print(f"[advertiser] invitation from {peer.displayName()} -> accept")
        handler(True, self.session)

    def advertiser_didNotStartAdvertisingPeer_(self, advertiser, err):
        print(f"[advertiser] error: {err}")

    # --- MCNearbyServiceBrowserDelegate ---

    def browser_foundPeer_withDiscoveryInfo_(self, browser, peer, info):
        if peer.displayName() == self.peer_id.displayName():
            return
        print(f"[browser] found {peer.displayName()} -> invite")
        browser.invitePeer_toSession_withContext_timeout_(peer, self.session, None, 30.0)

    def browser_lostPeer_(self, browser, peer):
        print(f"[browser] lost {peer.displayName()}")

    def browser_didNotStartBrowsingForPeers_(self, browser, err):
        print(f"[browser] error: {err}")


def run_runloop():
    rl = NSRunLoop.currentRunLoop()
    while True:
        rl.runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="display name for this peer")
    ap.add_argument("--service", default="synth-chat",
                    help="serviceType (1-15 chars, lowercase ASCII/digits/hyphen)")
    args = ap.parse_args()

    peer_id = MCPeerID.alloc().initWithDisplayName_(args.name)
    delegate = MPCDelegate.alloc().initWithPeer_service_(peer_id, args.service)
    delegate.start()

    # Run Cocoa runloop in background; main thread reads stdin.
    t = threading.Thread(target=run_runloop, daemon=True)
    t.start()

    print("Type a message and press enter. Ctrl-D / Ctrl-C to quit.")
    try:
        for line in sys.stdin:
            line = line.rstrip("\n")
            if not line:
                continue
            delegate.send_text(line)
    except KeyboardInterrupt:
        pass
    finally:
        delegate.stop()
        print("\n[mpc] stopped")


if __name__ == "__main__":
    main()
