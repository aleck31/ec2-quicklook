new Vue({
  el: '#app',
  delimiters: ['[[', ']]'],  // Set delimiters for this instance
  mounted() {
    // Remove v-cloak after Vue is mounted
    this.$el.removeAttribute('v-cloak');
  },
  data: {
    form: {
      region: 'us-east-1',
      arch: 'x86_64',
      operation: '',
      family: '',
      type: '',
      voltype: 'gp3',
      volsize: 60
    },
    loading: false,
    validated: false,
    instance: null,
    volume: null,
    previousPrice: null,
    comparisonItems: [],
    regionOptions: [],
    operationOptions: [],
    familyOptions: [],
    typeOptions: [],
    voltypeOptions: [],
    detailUrl: null
  },
  computed: {
    priceChange() {
      if (!this.instance || !this.previousPrice) return null;
      const currentPrice = this.instance.listPrice.pricePerUnit.value;
      const change = ((currentPrice - this.previousPrice) / this.previousPrice) * 100;
      return change;
    },
    canCompare() {
      return this.instance && this.comparisonItems.length < 4;
    },
    hardwareItems() {
      return this.instance ? Object.entries(this.instance.hardwareSpecs).map(([key, value]) => ({
        key,
        value
      })) : [];
    },
    softwareItems() {
      return this.instance ? Object.entries(this.instance.softwareSpecs).map(([key, value]) => ({
        key,
        value
      })) : [];
    },
    featureItems() {
      return this.instance ? Object.entries(this.instance.productFeature).map(([key, value]) => ({
        key,
        value
      })) : [];
    },
    storageItems() {
      return this.instance ? Object.entries(this.instance.instanceStorage).map(([key, value]) => ({
        key,
        value
      })) : [];
    },
    volumeItems() {
      return this.volume ? Object.entries(this.volume.productSpecs).map(([key, value]) => ({
        key,
        value
      })) : [];
    },
    comparisonFields() {
      return [
        { key: 'type', label: 'Instance Type' },
        { key: 'price', label: 'Price' },
        { key: 'vcpu', label: 'vCPU' },
        { key: 'memory', label: 'Memory' },
        { key: 'network', label: 'Network Performance' }
      ];
    }
  },
  methods: {
    async quickLook() {
      this.loading = true;
      try {
        // Store previous price for comparison
        this.previousPrice = this.instance?.listPrice.pricePerUnit.value;

        // Query instance data
        const instanceResponse = await axios.get('product/instance', {
          params: {
            region: this.form.region,
            type: this.form.type,
            op: this.form.operation
          }
        });
        this.instance = instanceResponse.data;

        // Query volume data
        const volumeResponse = await axios.get('product/volume', {
          params: {
            region: this.form.region,
            type: this.form.voltype,
            size: this.form.volsize
          }
        });
        this.volume = volumeResponse.data;

        // Update detail URL
        this.detailUrl = `detail?region=${this.form.region}&type=${this.form.type}`;

      } catch (error) {
        console.error('Error fetching data:', error);
        this.$bvToast.toast('Failed to fetch data. Please try again.', {
          title: 'Error',
          variant: 'danger',
          solid: true
        });
      } finally {
        this.loading = false;
      }
    },
    async updateFamily() {
      try {
        const response = await axios.get('instance/family', {
          params: {
            region: this.form.region,
            arch: this.form.arch
          }
        });
        this.familyOptions = response.data.map(item => ({
          value: item.name,
          text: `${item.description}: ${item.name}`
        }));
        // Set default family if available
        if (this.familyOptions.length > 0) {
          const defaultFamily = this.familyOptions.find(f => ['m5', 'm6g'].includes(f.value));
          if (defaultFamily) {
            this.form.family = defaultFamily.value;
            this.updateTypes();
          }
        }
      } catch (error) {
        console.error('Error fetching families:', error);
      }
    },
    async updateTypes() {
      if (!this.form.family) return;
      
      try {
        const response = await axios.get('instance/types', {
          params: {
            region: this.form.region,
            arch: this.form.arch,
            family: this.form.family
          }
        });
        this.typeOptions = response.data.map(item => ({
          value: item.instanceType,
          text: item.instanceType
        }));
        // Sort instance types by size
        this.typeOptions.sort((a, b) => {
          const sizeA = a.value.match(/\d+/)[0];
          const sizeB = b.value.match(/\d+/)[0];
          return parseInt(sizeA) - parseInt(sizeB);
        });
      } catch (error) {
        console.error('Error fetching types:', error);
      }
    },
    addToComparison() {
      if (!this.instance || this.comparisonItems.length >= 4) return;

      const item = {
        type: this.form.type,
        price: `${this.instance.listPrice.pricePerUnit.currency}${this.instance.listPrice.pricePerUnit.value.toFixed(2)}/${this.instance.listPrice.unit}`,
        vcpu: this.instance.hardwareSpecs.vCPU,
        memory: this.instance.hardwareSpecs.Memory,
        network: this.instance.hardwareSpecs['Network Performance']
      };

      this.comparisonItems.push(item);
      this.$bvModal.show('compare-modal');
    }
  },
  watch: {
    'form.arch'() {
      this.updateFamily();
    },
    'form.region'() {
      this.updateTypes();
    },
    'form.family'() {
      this.updateTypes();
    }
  },
  async created() {
    try {
      // Load initial data
      const [regionResponse, operationResponse, voltypeResponse] = await Promise.all([
        axios.get('instance/regions'),
        axios.get('instance/operations'),
        axios.get('instance/voltypes')
      ]);

      this.regionOptions = regionResponse.data.map(region => ({
        value: region.code,
        text: `${region.code} ${region.name}`
      }));

      this.operationOptions = operationResponse.data.map(op => ({
        value: op.operation,
        text: op.platform
      }));

      this.voltypeOptions = voltypeResponse.data.map(vt => ({
        value: vt,
        text: vt
      }));

      // Set default values
      this.form.operation = this.operationOptions.find(op => op.text === 'Linux/UNIX')?.value;
      await this.updateFamily();

    } catch (error) {
      console.error('Error loading initial data:', error);
    }
  }
});
