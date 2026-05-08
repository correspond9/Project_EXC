import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, FlatList, ActivityIndicator } from 'react-native';
import api from '../lib/api';

interface Order {
  id: string;
  symbol: string;
  side: string;
  order_type: string;
  quantity: number;
  filled_quantity: number;
  price: number | null;
  status: string;
  created_at: string;
}

export default function TradeHistoryScreen() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get('/api/orders/history?limit=50')
      .then((res) => setOrders(res.data))
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

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Trade History</Text>
      {orders.length === 0 ? (
        <Text style={styles.empty}>No orders yet.</Text>
      ) : (
        <FlatList
          data={orders}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <View style={styles.card}>
              <View style={styles.row}>
                <Text style={styles.symbol}>{item.symbol}</Text>
                <View style={[styles.badge, item.side === 'BUY' ? styles.buy : styles.sell]}>
                  <Text style={styles.badgeText}>{item.side}</Text>
                </View>
                <View style={[styles.badge, getStatusStyle(item.status)]}>
                  <Text style={styles.badgeText}>{item.status}</Text>
                </View>
              </View>
              <View style={styles.details}>
                <Text style={styles.detail}>Type: {item.order_type}</Text>
                <Text style={styles.detail}>Qty: {item.quantity}</Text>
                {item.price != null && <Text style={styles.detail}>Price: {item.price.toLocaleString()}</Text>}
                <Text style={styles.detail}>{new Date(item.created_at).toLocaleDateString()}</Text>
              </View>
            </View>
          )}
          contentContainerStyle={{ paddingBottom: 24 }}
        />
      )}
    </View>
  );
}

function getStatusStyle(status: string) {
  if (status === 'FILLED') return { backgroundColor: 'rgba(34,197,94,0.2)' };
  if (status === 'CANCELLED') return { backgroundColor: 'rgba(239,68,68,0.2)' };
  return { backgroundColor: 'rgba(234,179,8,0.2)' };
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0d1117' },
  center: { flex: 1, backgroundColor: '#0d1117', justifyContent: 'center', alignItems: 'center' },
  title: { fontSize: 22, fontWeight: '700', color: '#e6edf3', margin: 16, marginTop: 52 },
  empty: { color: '#8b949e', textAlign: 'center', marginTop: 60 },
  card: {
    marginHorizontal: 16, marginBottom: 8, backgroundColor: '#161b22',
    borderRadius: 10, padding: 14, borderWidth: 1, borderColor: '#21262d',
  },
  row: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 },
  symbol: { fontSize: 14, fontWeight: '700', color: '#e6edf3', flex: 1 },
  badge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6 },
  buy: { backgroundColor: 'rgba(34,197,94,0.2)' },
  sell: { backgroundColor: 'rgba(239,68,68,0.2)' },
  badgeText: { fontSize: 10, fontWeight: '700', color: '#e6edf3' },
  details: { flexDirection: 'row', gap: 12, flexWrap: 'wrap' },
  detail: { fontSize: 11, color: '#8b949e' },
});
