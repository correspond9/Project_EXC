import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import api from '../lib/api';

interface WalletBalance {
  currency: string;
  available: number;
  locked: number;
}

interface FuturesPosition {
  symbol: string;
  side: string;
  size: number;
  entry_price: number;
  unrealised_pnl: number;
  leverage: number;
}

export default function PortfolioScreen() {
  const [balances, setBalances] = useState<WalletBalance[]>([]);
  const [positions, setPositions] = useState<FuturesPosition[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/api/wallet/balances'),
      api.get('/api/futures/positions'),
    ])
      .then(([walRes, posRes]) => {
        setBalances(walRes.data);
        setPositions(posRes.data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color="#3b82f6" />
      </View>
    );
  }

  const totalBalance = balances.reduce((s, b) => s + b.available + b.locked, 0);

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Portfolio</Text>

      {/* Total */}
      <View style={styles.totalCard}>
        <Text style={styles.totalLabel}>Total Balance</Text>
        <Text style={styles.totalValue}>
          {totalBalance.toLocaleString(undefined, { minimumFractionDigits: 2 })} USDT
        </Text>
      </View>

      {/* Balances */}
      <Text style={styles.sectionTitle}>Wallet Balances</Text>
      {balances.map((b) => (
        <View key={b.currency} style={styles.card}>
          <Text style={styles.currency}>{b.currency}</Text>
          <View style={styles.balanceRow}>
            <View>
              <Text style={styles.balLabel}>Available</Text>
              <Text style={styles.balValue}>{b.available.toFixed(4)}</Text>
            </View>
            <View style={{ alignItems: 'flex-end' }}>
              <Text style={styles.balLabel}>Locked</Text>
              <Text style={styles.balValue}>{b.locked.toFixed(4)}</Text>
            </View>
          </View>
        </View>
      ))}

      {/* Futures Positions */}
      {positions.length > 0 && (
        <>
          <Text style={styles.sectionTitle}>Open Futures Positions</Text>
          {positions.map((p, i) => (
            <View key={i} style={styles.card}>
              <View style={styles.posHeader}>
                <Text style={styles.posSymbol}>{p.symbol}</Text>
                <View style={[styles.sideBadge, p.side === 'LONG' ? styles.long : styles.short]}>
                  <Text style={styles.sideText}>{p.side} {p.leverage}×</Text>
                </View>
              </View>
              <View style={styles.balanceRow}>
                <View>
                  <Text style={styles.balLabel}>Size</Text>
                  <Text style={styles.balValue}>{p.size}</Text>
                </View>
                <View>
                  <Text style={styles.balLabel}>Entry</Text>
                  <Text style={styles.balValue}>{p.entry_price.toLocaleString()}</Text>
                </View>
                <View style={{ alignItems: 'flex-end' }}>
                  <Text style={styles.balLabel}>uPnL</Text>
                  <Text style={[styles.balValue, { color: p.unrealised_pnl >= 0 ? '#22c55e' : '#ef4444' }]}>
                    {p.unrealised_pnl >= 0 ? '+' : ''}{p.unrealised_pnl.toFixed(2)}
                  </Text>
                </View>
              </View>
            </View>
          ))}
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0d1117' },
  center: { flex: 1, backgroundColor: '#0d1117', justifyContent: 'center', alignItems: 'center' },
  title: { fontSize: 22, fontWeight: '700', color: '#e6edf3', margin: 16, marginTop: 52 },
  totalCard: {
    margin: 16, backgroundColor: '#1d2d50', borderRadius: 12, padding: 20, alignItems: 'center',
  },
  totalLabel: { color: '#8b949e', fontSize: 13 },
  totalValue: { color: '#3b82f6', fontSize: 26, fontWeight: '700', marginTop: 4 },
  sectionTitle: { fontSize: 13, fontWeight: '600', color: '#8b949e', marginHorizontal: 16, marginTop: 8, marginBottom: 4 },
  card: {
    marginHorizontal: 16, marginBottom: 8, backgroundColor: '#161b22',
    borderRadius: 10, padding: 14, borderWidth: 1, borderColor: '#21262d',
  },
  currency: { fontSize: 15, fontWeight: '700', color: '#e6edf3', marginBottom: 8 },
  balanceRow: { flexDirection: 'row', justifyContent: 'space-between' },
  balLabel: { fontSize: 11, color: '#8b949e' },
  balValue: { fontSize: 14, color: '#e6edf3', fontWeight: '600' },
  posHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  posSymbol: { fontSize: 15, fontWeight: '700', color: '#e6edf3' },
  sideBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6 },
  long: { backgroundColor: 'rgba(34,197,94,0.2)' },
  short: { backgroundColor: 'rgba(239,68,68,0.2)' },
  sideText: { fontSize: 11, fontWeight: '700', color: '#e6edf3' },
});
