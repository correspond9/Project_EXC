import React, { useEffect, useState, useRef } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  TextInput, ActivityIndicator, Alert,
} from 'react-native';
import api from '../lib/api';
import { useAuthStore } from '../store/authStore';

interface Ticker {
  symbol: string;
  price: string;
  change: string;
}

export default function DashboardScreen() {
  const { tradingMode } = useAuthStore();
  const [tickers, setTickers] = useState<Ticker[]>([]);
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [side, setSide] = useState<'BUY' | 'SELL'>('BUY');
  const [quantity, setQuantity] = useState('');
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT'>('MARKET');
  const [price, setPrice] = useState('');
  const [placing, setPlacing] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Fetch initial ticker list
    api.get('/api/market/tickers').then((res) => setTickers(res.data)).catch(() => {});
  }, []);

  async function placeOrder() {
    if (!quantity) { Alert.alert('Error', 'Enter quantity.'); return; }
    setPlacing(true);
    try {
      const body: any = {
        symbol, side, quantity: parseFloat(quantity), order_type: orderType,
      };
      if (orderType === 'LIMIT') body.price = parseFloat(price);
      await api.post('/api/orders/spot', body);
      Alert.alert('Order Placed', `${side} ${quantity} ${symbol} order submitted.`);
      setQuantity('');
      setPrice('');
    } catch (err: any) {
      Alert.alert('Error', err?.response?.data?.detail || 'Order failed.');
    } finally {
      setPlacing(false);
    }
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Dashboard</Text>
        <View style={[styles.modeBadge, tradingMode === 'LIVE' ? styles.modeLive : styles.modeSim]}>
          <Text style={styles.modeText}>{tradingMode}</Text>
        </View>
      </View>

      {/* Market Prices */}
      <Text style={styles.sectionTitle}>Market Prices</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.tickerRow}>
        {tickers.slice(0, 10).map((t) => (
          <TouchableOpacity
            key={t.symbol}
            style={[styles.tickerCard, symbol === t.symbol && styles.tickerCardActive]}
            onPress={() => setSymbol(t.symbol)}
            accessibilityLabel={`Select ${t.symbol} trading pair`}
            accessibilityRole="button"
          >
            <Text style={styles.tickerSymbol}>{t.symbol.replace('USDT', '')}</Text>
            <Text style={styles.tickerPrice}>${parseFloat(t.price).toLocaleString()}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Order Form */}
      <Text style={styles.sectionTitle}>Place Order — {symbol}</Text>
      <View style={styles.card}>
        {/* Side */}
        <View style={styles.row}>
          {(['BUY', 'SELL'] as const).map((s) => (
            <TouchableOpacity
              key={s}
              style={[styles.sideBtn, side === s && (s === 'BUY' ? styles.sideBuy : styles.sideSell)]}
              onPress={() => setSide(s)}
              accessibilityLabel={`${s} order`}
              accessibilityRole="radio"
              accessibilityState={{ checked: side === s }}
            >
              <Text style={[styles.sideBtnText, side === s && styles.sideBtnTextActive]}>{s}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Type */}
        <View style={[styles.row, { marginTop: 8 }]}>
          {(['MARKET', 'LIMIT'] as const).map((t) => (
            <TouchableOpacity
              key={t}
              style={[styles.typeBtn, orderType === t && styles.typeBtnActive]}
              onPress={() => setOrderType(t)}
              accessibilityLabel={`${t} order type`}
            >
              <Text style={[styles.typeBtnText, orderType === t && styles.typeBtnTextActive]}>{t}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {orderType === 'LIMIT' && (
          <TextInput
            style={styles.input}
            placeholder="Limit Price (USDT)"
            placeholderTextColor="#8b949e"
            keyboardType="decimal-pad"
            value={price}
            onChangeText={setPrice}
            accessibilityLabel="Limit price"
          />
        )}

        <TextInput
          style={styles.input}
          placeholder="Quantity"
          placeholderTextColor="#8b949e"
          keyboardType="decimal-pad"
          value={quantity}
          onChangeText={setQuantity}
          accessibilityLabel="Order quantity"
        />

        <TouchableOpacity
          style={[styles.orderBtn, side === 'BUY' ? styles.orderBtnBuy : styles.orderBtnSell]}
          onPress={placeOrder}
          disabled={placing}
          accessibilityLabel={`Place ${side} order`}
          accessibilityRole="button"
        >
          {placing ? <ActivityIndicator color="#fff" /> : (
            <Text style={styles.orderBtnText}>{side} {symbol}</Text>
          )}
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0d1117' },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 16, paddingTop: 52 },
  title: { fontSize: 22, fontWeight: '700', color: '#e6edf3' },
  modeBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  modeLive: { backgroundColor: 'rgba(239,68,68,0.2)' },
  modeSim: { backgroundColor: 'rgba(59,130,246,0.2)' },
  modeText: { fontSize: 11, fontWeight: '600', color: '#e6edf3' },
  sectionTitle: { fontSize: 13, fontWeight: '600', color: '#8b949e', marginHorizontal: 16, marginTop: 16, marginBottom: 8 },
  tickerRow: { paddingLeft: 16 },
  tickerCard: {
    backgroundColor: '#161b22', borderRadius: 8, padding: 10, marginRight: 8,
    borderWidth: 1, borderColor: '#21262d', minWidth: 90,
  },
  tickerCardActive: { borderColor: '#3b82f6' },
  tickerSymbol: { fontSize: 12, fontWeight: '700', color: '#e6edf3', marginBottom: 2 },
  tickerPrice: { fontSize: 11, color: '#8b949e' },
  card: { margin: 16, backgroundColor: '#161b22', borderRadius: 12, padding: 16, borderWidth: 1, borderColor: '#21262d' },
  row: { flexDirection: 'row', gap: 8 },
  sideBtn: { flex: 1, padding: 12, borderRadius: 8, borderWidth: 1, borderColor: '#21262d', alignItems: 'center' },
  sideBuy: { backgroundColor: 'rgba(34,197,94,0.15)', borderColor: '#22c55e' },
  sideSell: { backgroundColor: 'rgba(239,68,68,0.15)', borderColor: '#ef4444' },
  sideBtnText: { fontWeight: '700', color: '#8b949e' },
  sideBtnTextActive: { color: '#e6edf3' },
  typeBtn: { flex: 1, padding: 8, borderRadius: 6, borderWidth: 1, borderColor: '#21262d', alignItems: 'center' },
  typeBtnActive: { borderColor: '#3b82f6' },
  typeBtnText: { fontSize: 12, color: '#8b949e' },
  typeBtnTextActive: { color: '#3b82f6' },
  input: {
    backgroundColor: '#0d1117', borderWidth: 1, borderColor: '#21262d', borderRadius: 8,
    padding: 12, color: '#e6edf3', marginTop: 10, fontSize: 14,
  },
  orderBtn: { marginTop: 12, padding: 14, borderRadius: 8, alignItems: 'center' },
  orderBtnBuy: { backgroundColor: '#22c55e' },
  orderBtnSell: { backgroundColor: '#ef4444' },
  orderBtnText: { color: '#fff', fontWeight: '700', fontSize: 15 },
});
