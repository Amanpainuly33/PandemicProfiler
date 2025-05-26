import React, { useState, useEffect } from 'react';
import { format } from 'date-fns';
import {
  Box,
  Container,
  Paper,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  CircularProgress,
  Card,
  CardContent,
  Grid,
  useTheme,
  alpha,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import PeopleIcon from '@mui/icons-material/People';
import LocalHospitalIcon from '@mui/icons-material/LocalHospital';
import type { CovidData, PredictionData, GrowthRateData, RecoveryRateData } from '../services/api';
import api from '../services/api';

const DEFAULT_START_DATE = new Date('2020-01-22');
const DEFAULT_END_DATE = new Date('2020-08-12');

const Dashboard: React.FC = () => {
  const theme = useTheme();
  const [states, setStates] = useState<string[]>([]);
  const [selectedState, setSelectedState] = useState<string>('');
  const [startDate, setStartDate] = useState<Date | null>(DEFAULT_START_DATE);
  const [endDate, setEndDate] = useState<Date | null>(DEFAULT_END_DATE);
  const [loading, setLoading] = useState(false);
  const [covidData, setCovidData] = useState<CovidData | null>(null);
  const [predictions, setPredictions] = useState<PredictionData | null>(null);
  const [growthRate, setGrowthRate] = useState<GrowthRateData | null>(null);
  const [recoveryRate, setRecoveryRate] = useState<RecoveryRateData | null>(null);

  useEffect(() => {
    loadStates();
    if (startDate && endDate) {
      loadData();
    }
  }, []);

  const loadStates = async () => {
    try {
      const statesList = await api.getStates();
      setStates(statesList);
    } catch (error) {
      console.error('Error loading states:', error);
    }
  };

  const loadData = async () => {
    if (!startDate || !endDate) return;

    setLoading(true);
    try {
      const [data, preds, growth, recovery] = await Promise.all([
        api.getData(selectedState, startDate.toISOString(), endDate.toISOString()),
        api.getPredictions(selectedState),
        api.getGrowthRate(selectedState),
        api.getRecoveryRate(selectedState),
      ]);

      setCovidData(data);
      setPredictions(preds);
      setGrowthRate(growth);
      setRecoveryRate(recovery);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getLatestStats = () => {
    if (!covidData || !covidData.confirmed || !covidData.deaths || !covidData.cured) return null;
    const lastIndex = covidData.confirmed.length - 1;
    if (lastIndex < 0) return null;
    
    return {
      confirmed: covidData.confirmed[lastIndex] || 0,
      deaths: covidData.deaths[lastIndex] || 0,
      cured: covidData.cured[lastIndex] || 0,
      growthRate: growthRate?.growth_rate?.[lastIndex] || 0,
      recoveryRate: recoveryRate?.recovery_rate?.[lastIndex] || 0,
    };
  };

  const stats = getLatestStats();

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box sx={{ 
        minHeight: '100vh',
        bgcolor: theme.palette.background.default,
        py: 4
      }}>
        <Container maxWidth="xl">
          <Box sx={{ mb: 4 }}>
            <Typography 
              variant="h3" 
              component="h1" 
              gutterBottom
              sx={{ 
                fontWeight: 'bold',
                color: theme.palette.primary.main,
                textAlign: 'center'
              }}
            >
              COVID-19 Dashboard
            </Typography>
            <Typography 
              variant="subtitle1" 
              sx={{ 
                textAlign: 'center',
                color: theme.palette.text.secondary,
                mb: 4
              }}
            >
              Track and analyze COVID-19 data across India
            </Typography>
          </Box>

          <Paper 
            elevation={0}
            sx={{ 
              p: 3, 
              mb: 4,
              borderRadius: 2,
              bgcolor: alpha(theme.palette.primary.main, 0.05)
            }}
          >
            <Grid container spacing={3} alignItems="center">
              <Grid item xs={12} sm={3}>
                <FormControl fullWidth>
                  <InputLabel>State</InputLabel>
                  <Select
                    value={selectedState}
                    label="State"
                    onChange={(e) => setSelectedState(e.target.value)}
                    sx={{ bgcolor: 'background.paper' }}
                  >
                    <MenuItem value="">All States</MenuItem>
                    {states.map((state) => (
                      <MenuItem key={state} value={state}>
                        {state}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={3}>
                <DatePicker
                  label="Start Date"
                  value={startDate}
                  onChange={setStartDate}
                  minDate={DEFAULT_START_DATE}
                  maxDate={endDate || DEFAULT_END_DATE}
                  slotProps={{ 
                    textField: { 
                      fullWidth: true,
                      sx: { bgcolor: 'background.paper' }
                    } 
                  }}
                />
              </Grid>
              <Grid item xs={12} sm={3}>
                <DatePicker
                  label="End Date"
                  value={endDate}
                  onChange={setEndDate}
                  minDate={startDate || DEFAULT_START_DATE}
                  maxDate={DEFAULT_END_DATE}
                  slotProps={{ 
                    textField: { 
                      fullWidth: true,
                      sx: { bgcolor: 'background.paper' }
                    } 
                  }}
                />
              </Grid>
              <Grid item xs={12} sm={3}>
                <Button
                  variant="contained"
                  onClick={loadData}
                  disabled={loading || !startDate || !endDate}
                  fullWidth
                  size="large"
                  sx={{ 
                    height: '56px',
                    borderRadius: 2,
                    textTransform: 'none',
                    fontSize: '1.1rem'
                  }}
                >
                  {loading ? <CircularProgress size={24} /> : 'Update Dashboard'}
                </Button>
              </Grid>
            </Grid>
          </Paper>

          {stats && (
            <Grid container spacing={3} sx={{ mb: 4 }}>
              <Grid item xs={12} sm={6} md={2.4}>
                <Card sx={{ 
                  borderRadius: 2,
                  bgcolor: alpha(theme.palette.error.main, 0.1)
                }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <PeopleIcon sx={{ color: theme.palette.error.main, mr: 1 }} />
                      <Typography variant="h6" color="text.secondary">
                        Confirmed Cases
                      </Typography>
                    </Box>
                    <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                      {stats.confirmed.toLocaleString()}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={2.4}>
                <Card sx={{ 
                  borderRadius: 2,
                  bgcolor: alpha(theme.palette.warning.main, 0.1)
                }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <LocalHospitalIcon sx={{ color: theme.palette.warning.main, mr: 1 }} />
                      <Typography variant="h6" color="text.secondary">
                        Deaths
                      </Typography>
                    </Box>
                    <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                      {stats.deaths.toLocaleString()}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={2.4}>
                <Card sx={{ 
                  borderRadius: 2,
                  bgcolor: alpha(theme.palette.success.main, 0.1)
                }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <TrendingUpIcon sx={{ color: theme.palette.success.main, mr: 1 }} />
                      <Typography variant="h6" color="text.secondary">
                        Recovered
                      </Typography>
                    </Box>
                    <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                      {stats.cured.toLocaleString()}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={2.4}>
                <Card sx={{ 
                  borderRadius: 2,
                  bgcolor: alpha(theme.palette.info.main, 0.1)
                }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <TrendingUpIcon sx={{ color: theme.palette.info.main, mr: 1 }} />
                      <Typography variant="h6" color="text.secondary">
                        Growth Rate
                      </Typography>
                    </Box>
                    <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                      {stats.growthRate.toFixed(2)}%
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={2.4}>
                <Card sx={{ 
                  borderRadius: 2,
                  bgcolor: alpha(theme.palette.secondary.main, 0.1)
                }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <TrendingDownIcon sx={{ color: theme.palette.secondary.main, mr: 1 }} />
                      <Typography variant="h6" color="text.secondary">
                        Recovery Rate
                      </Typography>
                    </Box>
                    <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                      {stats.recoveryRate.toFixed(2)}%
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}

          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Paper 
                elevation={0}
                sx={{ 
                  p: 3,
                  borderRadius: 2,
                  bgcolor: 'background.paper'
                }}
              >
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
                  COVID-19 Timeline
                </Typography>
                {covidData && covidData.dates && covidData.confirmed && covidData.deaths && covidData.cured && (
                  <ResponsiveContainer width="100%" height={400}>
                    <AreaChart data={covidData.dates.map((date, i) => ({
                      date: format(new Date(date), 'MMM d, yyyy'),
                      confirmed: covidData.confirmed[i],
                      deaths: covidData.deaths[i],
                      cured: covidData.cured[i],
                    }))}>
                      <defs>
                        <linearGradient id="confirmed" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={theme.palette.error.main} stopOpacity={0.8}/>
                          <stop offset="95%" stopColor={theme.palette.error.main} stopOpacity={0}/>
                        </linearGradient>
                        <linearGradient id="deaths" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={theme.palette.warning.main} stopOpacity={0.8}/>
                          <stop offset="95%" stopColor={theme.palette.warning.main} stopOpacity={0}/>
                        </linearGradient>
                        <linearGradient id="cured" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={theme.palette.success.main} stopOpacity={0.8}/>
                          <stop offset="95%" stopColor={theme.palette.success.main} stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Area type="monotone" dataKey="confirmed" stroke={theme.palette.error.main} fillOpacity={1} fill="url(#confirmed)" />
                      <Area type="monotone" dataKey="deaths" stroke={theme.palette.warning.main} fillOpacity={1} fill="url(#deaths)" />
                      <Area type="monotone" dataKey="cured" stroke={theme.palette.success.main} fillOpacity={1} fill="url(#cured)" />
                    </AreaChart>
                  </ResponsiveContainer>
                )}
              </Paper>
            </Grid>

            <Grid item xs={12} md={6}>
              <Paper 
                elevation={0}
                sx={{ 
                  p: 3,
                  borderRadius: 2,
                  bgcolor: 'background.paper'
                }}
              >
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
                  Predictions
                </Typography>
                {predictions && predictions.dates && predictions.predictions && predictions.lower_bound && predictions.upper_bound && (
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={predictions.dates.map((date, i) => ({
                      date,
                      prediction: predictions.predictions[i],
                      lower: predictions.lower_bound[i],
                      upper: predictions.upper_bound[i],
                    }))}>
                      <defs>
                        <linearGradient id="prediction" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={theme.palette.primary.main} stopOpacity={0.8}/>
                          <stop offset="95%" stopColor={theme.palette.primary.main} stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Area type="monotone" dataKey="prediction" stroke={theme.palette.primary.main} fillOpacity={1} fill="url(#prediction)" />
                      <Line type="monotone" dataKey="lower" stroke={theme.palette.primary.main} strokeDasharray="3 3" />
                      <Line type="monotone" dataKey="upper" stroke={theme.palette.primary.main} strokeDasharray="3 3" />
                    </AreaChart>
                  </ResponsiveContainer>
                )}
              </Paper>
            </Grid>

            <Grid item xs={12} md={6}>
              <Paper 
                elevation={0}
                sx={{ 
                  p: 3,
                  borderRadius: 2,
                  bgcolor: 'background.paper'
                }}
              >
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
                  Growth Rate
                </Typography>
                {growthRate && growthRate.dates && growthRate.growth_rate && (
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={growthRate.dates.map((date, i) => ({
                      date,
                      rate: growthRate.growth_rate[i],
                    }))}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line 
                        type="monotone" 
                        dataKey="rate" 
                        stroke={theme.palette.info.main}
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </Paper>
            </Grid>

            <Grid item xs={12}>
              <Paper 
                elevation={0}
                sx={{ 
                  p: 3,
                  borderRadius: 2,
                  bgcolor: 'background.paper'
                }}
              >
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
                  Recovery Rate
                </Typography>
                {recoveryRate && recoveryRate.dates && recoveryRate.recovery_rate && (
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={recoveryRate.dates.map((date, i) => ({
                      date,
                      rate: recoveryRate.recovery_rate[i],
                    }))}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line 
                        type="monotone" 
                        dataKey="rate" 
                        stroke={theme.palette.secondary.main}
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </Paper>
            </Grid>
          </Grid>
        </Container>
      </Box>
    </LocalizationProvider>
  );
};

export default Dashboard; 